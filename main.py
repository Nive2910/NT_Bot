from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters
)

import os

from db.database import init_db

from handlers.start_handler import handle_start
from handlers.text_handler import handle_text
from handlers.file_handler import (
    handle_files,
    handle_question
)

TOKEN = os.getenv("TOKEN")


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start))

    app.add_handler(CommandHandler(
        "askfile",
        handle_question
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text
    ))

    app.add_handler(MessageHandler(
        filters.Document.ALL,
        handle_files
    ))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        url_path="webhook",
        webhook_url=f"{os.getenv('WEBHOOK_URL')}/webhook"
    )


if __name__ == "__main__":
    init_db()
    main()