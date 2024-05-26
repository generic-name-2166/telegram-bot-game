import os
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
)
import warnings
from dataclasses import dataclass
from psycopg import Connection
from typing import Optional, Any

from db import connect_to_db, fetch_game
from monopoly import Game


async def help_(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("""List of commands
- /start to enter a game
- /begin to start a game with all the players who entered
- /help to show a list of available commands

In a game
- /roll to roll the dice
- /buy to buy current property
- /auction to put the property for auction
- /bid <price> to make a bid in the auction
- /rent to ask for rent payment
- /trade to initiate a trade
- /status to see game's status
""")


async def echo(update: Update, context: CallbackContext) -> None:
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass(init=False, slots=True)
class App(metaclass=Singleton):
    app: Application
    is_initialized: bool
    # A list of players that are ready per chat but aren't in a game
    # Remove upon entering a game
    # tuple is update.message.from_user.id and update.message.from_user.username
    ready: dict[int, list[tuple[int, Optional[str]]]]
    # update.message.chat.id
    games: dict[int, Game]
    db_conn: Connection

    def __init__(self) -> None:
        self.app: Application = (
            ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
        )

        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("begin", self.begin_command))
        self.app.add_handler(CommandHandler("roll", self.roll_command))
        self.app.add_handler(CommandHandler("buy", self.buy_command))
        self.app.add_handler(CommandHandler("auction", self.auction_command))
        self.app.add_handler(CommandHandler("bid", self.bid_command))
        self.app.add_handler(CommandHandler("rent", self.rent_command))
        self.app.add_handler(CommandHandler("trade", self.trade_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("help", help_))
        # The order matters
        self.app.add_handler(MessageHandler(filters.TEXT, echo))

        self.games: dict[int, Game] = dict()
        self.ready: dict[int, list[tuple[int, Optional[str]]]] = dict()

        # A travesty that only is_initalized flag is holding back
        self.db_conn: Connection = None

        self.is_initialized: bool = False

    async def start(self, context: Any) -> None:
        if self.is_initialized:
            return
        await self.app.initialize()
        await self.app.start()

        self.db_conn: Connection = connect_to_db(context)

        self.is_initialized = True

    async def stop(self) -> None:
        if not self.is_initialized:
            return

        await self.app.stop()
        await self.app.shutdown()

        self.db_conn.close()

        self.is_initialized = False

    async def handle_update(self, body: dict) -> None:
        if not self.is_initialized:
            warnings.warn("Update without intialization")
            return

        try:
            update: Update = Update.de_json(body, bot=self.app.bot)
            await self.app.process_update(update)
        except BaseException as e:
            self.db_conn.rollback()
            await self.stop()
            raise e
        else:
            pass
            # self.db_conn.commit()

    def db_sync(self, chat_id: int) -> None:
        maybe_game: None | list[tuple[int, Optional[str]]] | Game = fetch_game(
            self.db_conn, chat_id
        )
        if maybe_game is None:
            # Nothing to sync
            return
        elif isinstance(maybe_game, list):
            self.ready[chat_id] = maybe_game
            return
        self.games[chat_id] = maybe_game

    async def start_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat_id

        self.db_sync(chat_id)

        if self.games.get(chat_id, None) is not None:
            await update.message.reply_text("A game already in progress")
            return

        user_id: int = update.message.from_user.id
        username: Optional[str] = update.message.from_user.username
        user: tuple[int, Optional[str]] = (user_id, username)

        if self.ready.get(chat_id, None) is None:
            self.ready[chat_id] = [user]
        else:
            self.ready[chat_id].append(user)

        await update.message.reply_text("You have entered a game")

    async def begin_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat.id
        self.db_sync(chat_id)

        # Check if there's already a game in progress
        # and that there are players ready to start
        ready_players: list[tuple[int, Optional[str]]] = self.ready.get(chat_id, [])
        game: Optional[Game] = self.games.get(chat_id, None)

        if game is None and len(ready_players) > 0:
            await update.message.reply_text("Beginning of the game")
            game: Game = Game(ready_players)
            del self.ready[chat_id]
            self.games[chat_id] = game
        elif game is not None:
            await update.message.reply_text("A game already in progress.")
        else:
            await update.message.reply_text("Not enough people are ready")

    async def roll_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat.id
        user_id: int = update.message.from_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output = game.roll(user_id)
        if len(output.out) > 0:
            await update.message.reply_text(output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

    async def buy_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat.id
        user_id: int = update.message.from_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output = game.buy(user_id)
        if len(output.out) > 0:
            await update.message.reply_text(output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

    async def auction_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat.id
        user_id: int = update.message.from_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output = game.auction(user_id)
        if len(output.out) > 0:
            await update.message.reply_text(output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

    async def bid_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat.id
        user_id: int = update.message.from_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output = game.bid(user_id)
        if len(output.out) > 0:
            await update.message.reply_text(output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

    async def rent_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat.id
        _user_id: int = update.message.from_user.id
        self.db_sync(chat_id)
        # TODO

    async def trade_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat.id
        _user_id: int = update.message.from_user.id
        self.db_sync(chat_id)
        # TODO

    async def status_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.message.chat.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        await update.message.reply_text(game.get_status())
