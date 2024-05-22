from telegram import Update
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
)


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("You have entered a game")


async def help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("""# List of commands
- `/start` to enter a game
- `/begin` to start a game with all the players who entered
- `/help` to show a list of available commands""")


async def begin(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("You have started a game")


async def echo(update: Update, context: CallbackContext) -> None:
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)


def add_all_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("begin", begin))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT, echo))
