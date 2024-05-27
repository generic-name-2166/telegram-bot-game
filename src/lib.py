import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
import warnings
from dataclasses import dataclass
from psycopg import Connection
from typing import Optional, Any

import db
from monopoly import Game


INLINE_BUTTONS: dict[int, InlineKeyboardButton] = {
    1: InlineKeyboardButton("start", callback_data="1"),
    2: InlineKeyboardButton("begin", callback_data="2"),
    3: InlineKeyboardButton("help", callback_data="3"),
    4: InlineKeyboardButton("roll", callback_data="4"),
    5: InlineKeyboardButton("buy", callback_data="5"),
    6: InlineKeyboardButton("auction", callback_data="6"),
    7: InlineKeyboardButton("bid", callback_data="7"),
    8: InlineKeyboardButton("rent", callback_data="8"),
    9: InlineKeyboardButton("trade", callback_data="9"),
    10: InlineKeyboardButton("finish", callback_data="10"),
    11: InlineKeyboardButton("status", callback_data="11"),
}


def match_button(command: int) -> tuple[InlineKeyboardButton]:
    return INLINE_BUTTONS[command]


def construct_keyboard(commands: tuple[int]) -> InlineKeyboardMarkup:
    result = tuple(map(match_button, commands))
    return InlineKeyboardMarkup.from_column(result)


async def reply(
    update: Update, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None
) -> None:
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.effective_chat:
        await update.effective_chat.send_message(text, reply_markup=reply_markup)
    else:
        warnings.warn("No chat found for update")


async def help_(update: Update, _context: CallbackContext) -> None:
    keyboard = tuple(INLINE_BUTTONS.values())
    reply_markup = InlineKeyboardMarkup.from_column(keyboard)
    text: str = """List of commands
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
- /finish to finish the game
- /status to see game's status
"""
    await reply(update, text, reply_markup=reply_markup)


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
    # tuple is update.effective_user.id and update.effective_user.username
    ready: dict[int, list[tuple[int, Optional[str]]]]
    # update.effective_chat.id
    games: dict[int, Game]
    db_conn: Connection

    def __init__(self) -> None:
        self.app: Application = (
            ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
        )

        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("begin", self.begin_command))
        self.app.add_handler(CommandHandler("help", help_))
        self.app.add_handler(CommandHandler("roll", self.roll_command))
        self.app.add_handler(CommandHandler("buy", self.buy_command))
        self.app.add_handler(CommandHandler("auction", self.auction_command))
        self.app.add_handler(CommandHandler("bid", self.bid_command))
        self.app.add_handler(CommandHandler("rent", self.rent_command))
        self.app.add_handler(CommandHandler("trade", self.trade_command))
        self.app.add_handler(CommandHandler("finish", self.finish_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CallbackQueryHandler(self.query))
        # The order matters
        self.app.add_handler(MessageHandler(filters.TEXT, echo))

        self.games: dict[int, Game] = dict()
        self.ready: dict[int, list[tuple[int, Optional[str]]]] = dict()

        # A travesty that only is_initalized flag is holding back
        self.db_conn: Connection = None  # type: ignore

        self.is_initialized: bool = False

    async def start(self, context: Any) -> None:
        if self.is_initialized:
            return
        await self.app.initialize()
        await self.app.start()

        self.db_conn: Connection = db.connect_to_db(context)

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
        maybe_game: None | list[tuple[int, Optional[str]]] | Game = db.fetch_game(
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
        chat_id: int = update.effective_chat.id
        self.db_sync(chat_id)

        if chat_id in self.games.keys():
            await reply(update, "A game is already in progress")
            return

        user_id: int = update.effective_user.id
        username: Optional[str] = update.effective_user.username
        user: tuple[int, Optional[str]] = (user_id, username)

        if chat_id not in self.ready.keys():
            self.ready[chat_id] = [user]
        else:
            self.ready[chat_id].append(user)

        await reply(update, "You have entered a game")
        db.add_user(self.db_conn, chat_id, user_id, username)

    async def begin_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        self.db_sync(chat_id)

        # Check if there's already a game in progress
        # and that there are players ready to start
        ready_players: list[tuple[int, Optional[str]]] = self.ready.get(chat_id, [])
        game: Optional[Game] = self.games.get(chat_id, None)

        if len(ready_players) <= 0:
            await reply(update, "Not enough people are ready")
            return
        elif game is not None:
            await reply(update, "A game is already in progress.")
            return

        await reply(update, "Beginning of the game")
        game: Game = Game(ready_players)
        self.games[chat_id] = game
        db.begin_game(chat_id, tuple(map(lambda x: x[0], ready_players)))
        del self.ready[chat_id]

    async def roll_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        user_id: int = update.effective_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output, maybe_change = game.roll(user_id)
        if maybe_change is None:
            # TODO change types to indicate this better
            # No change
            return

        await reply(update, output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

        position, money = maybe_change
        db.roll_user(self.db_conn, chat_id, user_id, position, money)

    async def buy_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        user_id: int = update.effective_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output, maybe_money = game.buy(user_id)
        if len(output.out) > 0:
            await reply(update, output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

        if maybe_money is not None:
            db.buy_user(self.db_conn, chat_id, user_id, maybe_money)

    async def auction_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        user_id: int = update.effective_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output = game.auction(user_id)
        if len(output.out) > 0:
            await reply(update, output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

    async def bid_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        user_id: int = update.effective_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output = game.bid(user_id)
        if len(output.out) > 0:
            await reply(update, output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

    async def rent_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        _user_id: int = update.effective_user.id
        self.db_sync(chat_id)
        # TODO

    async def trade_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        _user_id: int = update.effective_user.id
        self.db_sync(chat_id)
        # TODO

    async def finish_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        _user_id: int = update.effective_user.id
        self.db_sync(chat_id)
        # TODO

    async def status_command(self, update: Update, context: CallbackContext) -> None:
        chat_id: int = update.effective_chat.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        await reply(update, game.get_status())

    async def query(self, update: Update, context: CallbackContext) -> None:
        query: CallbackQuery = update.callback_query

        command: str = query.data
        if command == "1":
            await self.start_command(update, context)
        elif command == "2":
            await self.begin_command(update, context)
        elif command == "3":
            await help_(update, context)
        elif command == "4":
            await self.roll_command(update, context)
        elif command == "5":
            await self.buy_command(update, context)
        elif command == "6":
            await self.auction_command(update, context)
        elif command == "7":
            await self.bid_command(update, context)
        elif command == "8":
            await self.rent_command(update, context)
        elif command == "9":
            await self.trade_command(update, context)
        elif command == "10":
            await self.finish_command(update, context)
        elif command == "11":
            await self.status_command(update, context)
        # else should be unreachable

        await query.answer()
