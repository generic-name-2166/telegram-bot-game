from typing import Optional
import json
import os
import warnings
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters


def get_body(event: Optional[dict]) -> Optional[dict]:
    try:
        result = json.loads(event.get("body", "null")) if event is not None else None
    except json.JSONDecodeError:
        result = None
    return result


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Bot started")


async def echo(update: Update, context: CallbackContext) -> None:
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)


class App(metaclass=Singleton):
    def __init__(self) -> None:
        self.app: Application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
        
        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(MessageHandler(filters.TEXT, echo))

        self.is_initialized: bool = False

    async def start(self) -> None:
        if self.is_initialized:
            return
        await self.app.initialize()
        await self.app.start()

        self.is_initialized = True

    async def stop(self) -> None:
        if not self.is_initialized:
            return
        await self.app.stop()
        await self.app.shutdown()
        self.is_initialized = False

    async def handle_update(self, body: dict) -> None:
        try:
            update: Update = Update.de_json(body, bot=None)
            warnings.warn("Processing")
            await self.app.process_update(update)
        except BaseException:
            await self.stop()


async def handler(event: Optional[dict], context: Optional[dict]) -> dict:
    body: Optional[dict] = get_body(event)
    if body is not None:
        app: App = App()
        await app.handle_update(body)
    return {
        "statusCode": 200,
        "body": "",
    }
