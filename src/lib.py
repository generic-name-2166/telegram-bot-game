import os
import asyncio
import warnings
from telegram import Bot, Update
from telegram.error import Forbidden, NetworkError


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


async def echo(update: Update) -> None:
    if update.message and update.message.text:
        # Reply to the message
        await update.message.reply_text(update.message.text)


class App(metaclass=Singleton):
    def __init__(self) -> None:
        self.bot: Bot = Bot(os.environ["BOT_TOKEN"])
        self.update_id: int = 0
        self.is_initialized: bool = False

    async def start(self) -> None:
        if self.is_initialized:
            return
        await self.bot.set_webhook(
            url="https://d5d03fs5mutqpqb4qddc.apigw.yandexcloud.net/echo",
            allowed_updates=Update.ALL_TYPES,
        )

        await self.bot.initialize()

        try:
            self.update_id = (await self.bot.get_updates())[0].update_id
        except IndexError:
            self.update_id = 0

        self.is_initialized = True

    async def stop(self) -> None:
        if not self.is_initialized:
            return
        await self.bot.shutdown()
        self.is_initialized = False

    async def handle(self) -> None:
        try:
            updates: list[Update] = await self.bot.get_updates(
                offset=self.update_id,
                timeout=10,
                allowed_updates=Update.ALL_TYPES,
            )
            warnings.warn(str(updates))
            for update in updates:
                self.update_id += 1
                await echo(update)
                return
            return
        except NetworkError:
            await asyncio.sleep(1)
            warnings.warn("Network Error")
        except Forbidden:
            self.update_id += 1
            warnings.warn("Blocked")
        except BaseException:
            warnings.warn("Shutting down")
            await self.stop()
