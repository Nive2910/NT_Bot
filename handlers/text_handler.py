from telegram import Update
from telegram.ext import ContextTypes

from db.database import (
    load_memory,
    save_message
)

from services.ai_service import ask_ai

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