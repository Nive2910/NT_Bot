from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq
import os
import sqlite3
import pytesseract
from PIL import Image
from docx import Document
import PyPDF2
import pandas as pd

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

conn = sqlite3.connect("bot.db", check_same_thread= False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS chat_history(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, role TEXT, content TEXT)""")
conn.commit()

def save_message(user_id, role, content):
    cursor.execute("INSERT INTO chat_history(user_id, role, content) VALUES(?,?,?)",(user_id, role,content))
    conn.commit()

def load_memory(user_id):
    cursor.execute("""SELECT role,content FROM chat_history WHERE user_id =? ORDER BY id DESC LIMIT 30""",(user_id,))
    rows = cursor.fetchall()
    rows.reverse()
    return [{"role":r[0],"content":r[1]} for r in rows]

def chunk_text(text,size=1000):
    return [text[i:i+size] for i in range(0,len(text),size)]

def read_pdf(file_path):
    text=""
    with open(file_path,"rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or " "
    return text
def read_txt(file_path):
    with open(file_path,"r", encoding="UTF-8") as f:
        return f.read()
    
def read_docx(file_path):
    doc= Document(file_path)
    text="" 
    for para in doc.paragraphs:
        text+=para.text +"\n"
    return text
def read_csv(file_path):
    df = pd.read_csv(file_path)
    return df.head(20).to_string()
def read_img(file_path):
    img = Image.open(file_path)
    return pytesseract.image_to_string(img)

def ask_ai(messages):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    return response.choices[0].message.content

async def handle_start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    keyboard =[["START AI"],["STOP AI"]]
    await update.message.reply_text("AI Ready", reply_markup= ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle_menu(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "START AI":
        context.user_data["ai_mode"] = True
        await update.message.reply_text("AI started.")

    elif text =="STOP AI":
        context.user_data["ai_mode"]= False
        await update.message.reply_text("AI stopped.")
    else:
        await update.message.reply_text("Select from choice")

async def handle_text(update:Update, context:ContextTypes.DEFAULT_TYPE):
    try:
        user_id =  update.message.from_user.id
        text =  update.message.text

        if context.user_data.get("ai_mode"):
            messages = load_memory(user_id)
            messages.append({"role": "user", "content": text})
            reply = ask_ai(messages)
            save_message(user_id,"user",text)
            save_message(user_id,"assistant", reply)
            await update.message.reply_text(reply)
    
        else:
            await update.message.reply_text("Need to select START AI")
    except Exception as e:
        print(e)
        await update.message.reply_text("Error Occurred")
    
async def handle_file(update:Update, context:ContextTypes.DEFAULT_TYPE):
    try:
        user_id =  update.message.from_user.id
        file =  update.message.document
        name = file.file_name.lower()
        
        os.makedirs("downloads",exist_ok=True)
        file_path = os.path.join("downloads", file.file_name)
        file_obj = await file.get_file()
        await file_obj.download_to_drive(file_path)

        if name.endswith(".pdf"):
           text = read_pdf(file_path)
        elif name.endswith(".txt"):
            text = read_txt(file_path)
        elif name.endswith(".docx"):
            text = read_docx(file_path)
        elif name.endswith(".csv"):
            text = read_csv(file_path)
        else:
            await update.message.reply_text("Unsupported file")
        
        if not text.strip():
            await update.message.reply_text("No text found")
            return
        
        chunks = chunk_text(text)
        result =""


        for chunk in chunks[:3]:
            prompt = f"Explain or summarize this data:\n{chunk}"
            messages = load_memory(user_id)
            messages.append({"role": "user", "content": prompt})

            reply = ask_ai(messages)

            save_message(user_id, "user", prompt)
            save_message(user_id,"assistant", reply)

            result += reply + "\n"

        await update.message.reply_text(result[:4000])


    except Exception as e:
        print(e)
        await update.message.reply_text("Error Occurred")

async def handle_image(update:Update, context:ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        photo = update.message.photo[-1]
        
        os.makedirs("downloads", exist_ok=True)
        file_path = os.path.join("downloads", "image.jpg")

        file_obj = await photo.get_file()
        await file_obj.download_to_drive(file_path)

        text = read_img(file_path)

        if not text.strip():
            await update.message.reply_text("No text found")
            return
        
        messages = load_memory(user_id)
        messages.append({"role": "user", "content": text})

        reply = ask_ai(messages)

        save_message(user_id,"user", text)
        save_message(user_id, "assistant", reply)

        await update.message.reply_text(reply[:4000])


    except Exception as e:
        print(e)
        await update.message.reply_text("error occurred")


def main():

    app= ApplicationBuilder().token(Token).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.Regex("^(START AI|STOP AI)$"), handle_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    app.run_polling()

if __name__ =="__main__":
    main()




    
