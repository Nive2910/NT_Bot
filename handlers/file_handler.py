from telegram import Update
from telegram.ext import ContextTypes
import os

from db.database import (
    save_file_summary,
    load_file_summary,
    load_memory,
    save_message
)

from services.ai_service import ask_ai

from utils.file_reader import (
    read_pdf,
    read_text,
    read_docx,
    read_csv,
    chunk_text
)
async def handle_files(update:Update, context:ContextTypes.DEFAULT_TYPE):
        try:
            user_id= update.message.from_user.id
            file =update.message.document
            name = file.file_name.lower()
            os.makedirs("downloads",exist_ok=True)
            file_path= os.path.join("downloads",f"{user_id}_{file.file_name}")
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

            await update.message.reply_text(f"Here is the Summary of the content: {combined_summary}")
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
                    return
                file_name, summary = file_data

                question = " ".join(context.args)

                if not question:
                    await update.message.reply_text("use /askfile")
                    return
                messages = load_memory(user_id)
                messages.append({"role":"system", "content":f"File {file_name} Summary:{summary}"})
                messages.append({"role":"user", "content":question})
                reply = ask_ai(messages)
                await update.message.reply_text(reply)
                save_message(user_id, "user", question)
                save_message(user_id, "assistant", reply)


            except Exception as e:
                print(e)
                await update.message.reply_text("Error Occurred")
