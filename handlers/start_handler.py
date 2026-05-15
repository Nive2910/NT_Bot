from telegram import Update
from telegram.ext import ContextTypes

async def handle_start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        " AI Bot Ready\n"
        "Send a message to chat with AI.\n"
        "Upload PDF/TXT/DOCX/CSV files for summary.\n"
        "Use /askfile <question> to ask questions from uploaded file."
    )
