# I hate this project structure
import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


def main(event: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Handle restarts here, somehow
    # TODO
    application = ApplicationBuilder().token(os.environ()).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    application.insert_callback_data(event)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "event": event,
                "context": context,
            },
            default=vars,
        ),
    }


if __name__ == "__main__":
    main()
