from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
import os
from groq import Groq
from docx import Document
import PyPDF2
import pandas as pd

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TOKEN= os.getenv("TOKEN")
client = Groq(api_key=GROQ_API_KEY)

DB_PATH = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS chat_history(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER, role TEXT, content TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_files(user_id INTEGER PRIMARY KEY, file_name TEXT, summary TEXT)""")
    conn.commit()
    conn.close()

def save_message(user_id,role,content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
         "INSERT INTO chat_history(user_id, role, content) VALUES(?,?,?)",
        (user_id, role, content)
    )
    conn.commit()
    conn.close()

def load_memory(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role,content FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT 20",(user_id,))
    rows  = cursor.fetchall()
    conn.close()
    rows.reverse()
    return [{"role":r[0],"content":r[1]} for r in rows]

def save_file_summary(user_id, file_name, summary):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_files(user_id, file_name, summary) values (?,?,?)",(user_id, file_name,summary))
    conn.commit()
    conn.close()

def load_file_summary(user_id):
    conn=sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, summary FROM user_files WHERE user_id = ?",(user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def chunk_text(text, size=1500):
    return [text[i:i+size] for i in range(0,len(text),size)]

def ask_ai(messages):
    response=client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    return response.choices[0].message.content

def read_text(file_path):
    with open(file_path,"r") as f:
        return f.read()

def read_pdf(file_path):
    text=""
    with open(file_path,"rb") as f:
        reader = PyPDF2.PdfFileReader(f)
        for page in reader.pages:
            text += page.extract_text() or " "

    return text

def read_docx(file_path):
    text= ""
    doc = Document(file_path)
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def read_csv(file_path):
    df = pd.read_csv(file_path)
    return [df.head(20).to_string()]

async def handle_start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        " AI Bot Ready\n"
        "Send a message to chat with AI.\n"
        "Upload PDF/TXT/DOCX/CSV files for summary.\n"
        "Use /askfile <question> to ask questions from uploaded file."
    )


async def handle_text(update:Update, context:ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        text= update.message.text
        messages = load_memory(user_id)
        messages.append({"role":"user", "content":text})

        reply = ask_ai(messages)
        messages.append({"role":"assistant", "content": reply})

        save_message(user_id,"user",text)
        save_message(user_id,"assistant",reply)

        await update.message.reply_text(reply)
        
    except Exception as e:
        print(e)
        await update.message.reply_text("Error occurred")

async def handle_files(update:Update, context:ContextTypes.DEFAULT_TYPE):
        try:
            user_id= update.message.from_user.id
            file =update.message.document
            name = file.file_name.lower()
            os.makedirs("downloads",exist_ok=True)
            file_path= os.path.join("downloads",f"{user_id}.{file.file_name}")
            file_obj = await file.get_file()
            await file_obj.download_to_drive(file_path)
            text =""
            if name.endswith(".pdf"):
                text = read_pdf(file_path)
            elif name.endswith(".txt"):
                text=read_text(file_path)
            elif name.endswith(".csv"):
                text=read_csv(file_path)
            elif name.endswith(".docx"):
                text = read_docx(file_path)
            else:
                await update.message.reply_text("Unsupported file")
                return
            if not text.strip():
                await update.message.reply_text("No text found in uploaded file")
            
            chunks = chunk_text(text)
            combined_summary=""


            for chunk in chunks[:5]:
                messages=[{"role":"system", "content":"Summarize this content clearly" },{"role":"user", "content":chunk}]
                summary = ask_ai(messages)
                combined_summary += summary + "\n"

            save_file_summary(user_id,file.file_name,combined_summary)

            await update.message.reply_text("Uploaded file is processed. Use/askfile <question> to ask about this file")

        except Exception as e:
            print(e)
            await update.message.reply_text("Error Occurred")
        

async def handle_question(update:Update, context:ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.message.from_user.id
                file_data = load_file_summary(user_id)

                if not file_data:
                    await update.message.reply_text("No file uploaded yet")
                    
                file_name, summary = file_data

                question = " ".join(context.args)

                if not question:
                    await update.message.replyy_text("use /askfile")
                    return
                messages = load_memory(user_id)
                messages.append({"role":"system", "content":f"File {file_name} Summary:{summary}"})
                messages.append({"role":"user", "content":question})
                reply = ask_ai(messages)
                await update.message.reply_text(reply)


            except Exception as e:
                print(e)
                await update.message.reply_text("Error Occurred")

def main():

    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("START", handle_start))
    app.add_handler(CommandHandler("askfile", handle_question))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_files))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        url_path="webhook",
        webhook_url=f"{os.getenv('WEBHOOK_URL')}/webhook"
    )

if __name__=="__main__":
    init_db()
    main()
            
            
            






    
    




