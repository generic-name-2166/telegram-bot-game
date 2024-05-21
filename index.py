from typing import Optional
import json
import os
import warnings
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
)


def parse_body(message: dict) -> Optional[dict]:
    try:
        body = message["details"]["message"]["body"]
        result = json.loads(body) if message is not None else None
    except (json.JSONDecodeError, KeyError) as e:
        warnings.warn(f"JSON error {e}")
        result = None
    return result


def get_body(event: Optional[dict]) -> Optional[list[dict]]:
    if event is None:
        return None
    messages: Optional[list[dict]] = event.get("messages")
    if messages is None:
        return None
    return list(filter(lambda x: x is not None, map(parse_body, messages)))


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
        self.app: Application = (
            ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
        )

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
            update: Update = Update.de_json(body, bot=self.app.bot)
            warnings.warn("Processing")
            await self.app.process_update(update)
        except BaseException as e:
            warnings.warn(f"Exception occured {e}")
            await self.stop()


async def handler(event: Optional[dict], context: Optional[dict]) -> dict:
    bodies: Optional[list[dict]] = get_body(event)
    if bodies is not None:
        app: App = App()
        await app.start()
        warnings.warn(f"{len(bodies)=}")
        for body in bodies:
            await app.handle_update(body)
    else:
        warnings.warn(f"Body is empty {body}")
    return {
        "statusCode": 200,
        "body": "",
    }
