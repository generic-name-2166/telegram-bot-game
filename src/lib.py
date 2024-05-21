import os
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class App(metaclass=Singleton):
    def __init__(self) -> None:
        self.app: Application = (
            ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
        )

        start_handler: CommandHandler = CommandHandler("start", start)
        self.app.add_handler(start_handler)

        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    async def webserve(self, body: dict) -> None:
        async with self.app:
            await self.app.start()
            await self.app.update_queue.put(Update.de_json(data=body, bot=self.app.bot))
            await self.app.stop()
