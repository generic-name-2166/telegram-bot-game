import os
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
)
import warnings

from command import add_all_handlers


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

        add_all_handlers(self.app)

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
            await self.app.process_update(update)
        except BaseException as e:
            warnings.warn(f"Exception occured {e}")
            await self.stop()
