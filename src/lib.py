import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
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
    12: InlineKeyboardButton("map", callback_data="12"),
    13: InlineKeyboardButton("build", callback_data="13"),
}

MAPS: dict[int, str] = {
    0: "AgACAgIAAxkDAAICG2ZXcesdj44gCRfnxb_d7sUuAAFoDwACv90xGylbwEophxkgm9EeMAEAAwIAA3MAAzUE",
    1: "AgACAgIAAxkDAAICHmZXcgfj1edBLLL00Jx_3-0yqUG7AALB3TEbKVvASvhU1aoZ5jKsAQADAgADcwADNQQ",
    2: "AgACAgIAAxkDAAICIWZXchaZ2cmguZQWYbBtP4NqHGsPAALC3TEbKVvASsvO1Cu11hzXAQADAgADcwADNQQ",
    3: "AgACAgIAAxkDAAICJGZXckYL4jwtTs09GR0mbXYT7fN8AALE3TEbKVvASptMp8CqQ-lGAQADAgADcwADNQQ",
    4: "AgACAgIAAxkDAAICJ2ZXclNYWC6YW0xkQ__fXQjXE_M0AALF3TEbKVvASveR9VyqVqN1AQADAgADcwADNQQ",
    5: "AgACAgIAAxkDAAICKmZXcmdawWmvEZ9Z9KAC-6DsCMv4AALH3TEbKVvAShPgBmza1fnWAQADAgADcwADNQQ",
    6: "AgACAgIAAxkDAAICLWZXcne7eIKvOdv_3VBcwiH89VhDAALI3TEbKVvASoTOI4NJcd73AQADAgADcwADNQQ",
    7: "AgACAgIAAxkDAAICMGZXc5sLNbKG0oN6z1prTtwstwcXAALY3TEbKVvASm5j6G85bmSqAQADAgADcwADNQQ",
    8: "AgACAgIAAxkDAAICMWZXc7BOr6zfPf35PfDhbP1bxn46AALZ3TEbKVvASpW3nBDMXGB4AQADAgADcwADNQQ",
    9: "AgACAgIAAxkDAAICMmZXc72P7eBCkLert8gr371gG_DgAALb3TEbKVvASjQTqr7WEmRKAQADAgADcwADNQQ",
    10: "AgACAgIAAxkDAAICM2ZXc8Xkf_FoKAcAAdoMQzjn1nLB1AAC3N0xGylbwEo2ZJgh70Ky8AEAAwIAA3MAAzUE",
    11: "AgACAgIAAxkDAAICNGZXc83BsNjjXbOqtECOnv2erQABJQAC3d0xGylbwEpBIAq0dVkQlAEAAwIAA3MAAzUE",
    12: "AgACAgIAAxkDAAICNWZXc9Uj-rLSM3xy7Ta7MWXUk0kYAALe3TEbKVvASqwO3xFLCZFhAQADAgADcwADNQQ",
    13: "AgACAgIAAxkDAAICNmZXc9sISBjt0kebQNzhxPoefqatAALf3TEbKVvASszGmzfgT53-AQADAgADcwADNQQ",
    14: "AgACAgIAAxkDAAICN2ZXc-Zf2raRKeeLv05GoH-91nIKAALg3TEbKVvASmjTap8o-7hsAQADAgADcwADNQQ",
    15: "AgACAgIAAxkDAAICOGZXc-zHznV0tyagsL5GiT8fG9AYAALh3TEbKVvASrTlpx71132jAQADAgADcwADNQQ",
    16: "AgACAgIAAxkDAAICOWZXc_Oy8mR-MhNjZyoaiO1eQVN3AALl3TEbKVvASusmce34MXwPAQADAgADcwADNQQ",
    17: "AgACAgIAAxkDAAICOmZXc_p9S7birpdFQWCyLPaBEu4eAALm3TEbKVvASlguVN946MGvAQADAgADcwADNQQ",
    18: "AgACAgIAAxkDAAICO2ZXdCb6J4IFKqP2xX976V9if7LtAALn3TEbKVvASt0Snt4jz0Z1AQADAgADcwADNQQ",
    19: "AgACAgIAAxkDAAICPGZXdC5kJGgg7XPAaWf5eB8B5JOUAALo3TEbKVvASoRLwrJH-Zl2AQADAgADcwADNQQ",
    20: "AgACAgIAAxkDAAICPWZXdDYfl0NygMQ68dv47bxagAx7AALp3TEbKVvASkL7gjsKB36xAQADAgADcwADNQQ",
    21: "AgACAgIAAxkDAAICPmZXdECIS9WjiCHtBA_StT25AAHcxgAC6t0xGylbwErypvdjgO3YUgEAAwIAA3MAAzUE",
    22: "AgACAgIAAxkDAAICP2ZXdEaerNihk_WnBvG3kdeIefnvAALr3TEbKVvASr6QaJ2m7AJ-AQADAgADcwADNQQ",
    23: "AgACAgIAAxkDAAICQGZXdF-8WnVhMoMCnpihbK0wZK05AALs3TEbKVvASqPuK4Cs4-gxAQADAgADcwADNQQ",
    24: "AgACAgIAAxkDAAICQWZXdGWpm4sLQ1HX_gt7VlaZgOasAALt3TEbKVvAShM9U8Og1LsjAQADAgADcwADNQQ",
    25: "AgACAgIAAxkDAAICQmZXdIIb35IuoMYoYfGPksTLzE-tAALu3TEbKVvASpMrLCtVFYVJAQADAgADcwADNQQ",
    26: "AgACAgIAAxkDAAICQ2ZXdIlG6BQ1bmUR-wP5nz5MBHXEAALv3TEbKVvASphDf9o_oILmAQADAgADcwADNQQ",
    27: "AgACAgIAAxkDAAICRGZXdI9OfSz4hL6aCjWnjK5tagxJAALw3TEbKVvASkqkJcepy593AQADAgADcwADNQQ",
    28: "AgACAgIAAxkDAAICRWZXdJbqgTb5tPEhH80HJDwv3rBxAALx3TEbKVvASr28PRTK2yY5AQADAgADcwADNQQ",
    29: "AgACAgIAAxkDAAICRmZXdJ3qWzVahmGux5oN5FpyMncOAALy3TEbKVvASj7TKLbaGO28AQADAgADcwADNQQ",
    30: "AgACAgIAAxkDAAICR2ZXdKN3jxY8BOeE4wZMCylgeBZ0AALz3TEbKVvASt3unGwtr8yvAQADAgADcwADNQQ",
    31: "AgACAgIAAxkDAAICSGZXdKprmDM_0u1LDI8o1fZFH6u2AAL03TEbKVvAStjDnWoN-IOLAQADAgADcwADNQQ",
    32: "AgACAgIAAxkDAAICSWZXdLC6ZsZxLCHhCOv1mNbt3JBJAAL13TEbKVvASuL0IXX-6r4FAQADAgADcwADNQQ",
    33: "AgACAgIAAxkDAAICSmZXdLbrdQLJdc2Sf491haCHkRpqAAL23TEbKVvASh7TDlK9nHKsAQADAgADcwADNQQ",
    34: "AgACAgIAAxkDAAICS2ZXdL2hVLhGnV4wvl9V9xBl1cTPAAL33TEbKVvASvcVrS0k0Hs3AQADAgADcwADNQQ",
    35: "AgACAgIAAxkDAAICTGZXdMJb861hjbH6MqazCSaYAaBiAAL43TEbKVvASs8bzmTEZPK_AQADAgADcwADNQQ",
    36: "AgACAgIAAxkDAAICTWZXdMpPzOntbwo0GpIU8iUYGVy6AAL53TEbKVvASpd5xP3o0S_aAQADAgADcwADNQQ",
    37: "AgACAgIAAxkDAAICTmZXdNCxEDOmjyGoQT9xD4zqngPUAAL73TEbKVvASmavE_qsAAHaQQEAAwIAA3MAAzUE",
    38: "AgACAgIAAxkDAAICT2ZXdNeARfoYVrvwukYXsiwH9Oz5AAL83TEbKVvASh_5DLgtidLvAQADAgADcwADNQQ",
    39: "AgACAgIAAxkDAAICUGZXdOKYJ_wpmYDkbomjspMyqwrFAAL93TEbKVvASmxWZ3ThfYLyAQADAgADcwADNQQ",
    100: "AgACAgIAAxkDAAIB-2ZXHRJ_cAE0faxq-S7J7fY0dSGGAAKX4TEbKVu4Sl1ARUom521wAQADAgADcwADNQQ",
    101: "AgACAgIAAxkDAAICFmZXaxlh4-V6-WLoXPgQISre49Y8AAJo3TEbKVvASkZLh9El0_ujAQADAgADcwADNQQ",
}


def match_button(command: int) -> InlineKeyboardButton:
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


async def help_(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
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
- /map to see the board and your position
- /build <tile> to add a house to an owned street
"""
    await reply(update, text, reply_markup=reply_markup)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)


# async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     message = await update.effective_chat.send_photo("../assets/tile-39.png")
#     print(message.photo[0].file_id)


def is_ready(ready: list[tuple[int, Optional[str]]], user_id: int) -> bool:
    return user_id in {id_ for id_, _name in ready}


class Singleton(type):
    _instances: dict[Any, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any):
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
        self.app.add_handler(CommandHandler("map", self.map_command))
        self.app.add_handler(CommandHandler("build", self.build_command))
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

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
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
        elif is_ready(self.ready[chat_id], user_id):
            # User is already registered
            return
        else:
            self.ready[chat_id].append(user)

        keyboard = construct_keyboard((2,))
        await reply(update, "You have entered a game", reply_markup=keyboard)
        db.add_user(self.db_conn, chat_id, user_id, username)

    async def begin_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
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

        keyboard = construct_keyboard((4,))
        await reply(update, "Beginning of the game", reply_markup=keyboard)

        game: Game = Game(ready_players)
        self.games[chat_id] = game
        db.begin_game(self.db_conn, chat_id, tuple(map(lambda x: x[0], ready_players)))
        del self.ready[chat_id]

    async def roll_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
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
        position, money, status = maybe_change

        keyboard = construct_keyboard((5, 6, 12) if status == "buy" else (4, 12))

        await reply(update, output.out, reply_markup=keyboard)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

        db.roll_user(self.db_conn, chat_id, user_id, position, money, status)

    async def buy_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id: int = update.effective_chat.id
        user_id: int = update.effective_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output, maybe_purchase = game.buy(user_id)
        if len(output.warning) > 0:
            warnings.warn(output.warning)

        if len(output.out) > 0 and maybe_purchase is None:
            await reply(update, output.out)
        elif len(output.out) > 0:
            keyboard = construct_keyboard((4, 12))
            await reply(update, output.out, reply_markup=keyboard)

        if maybe_purchase is None:
            return
        money, tile_id = maybe_purchase
        db.buy_user(self.db_conn, chat_id, user_id, money, tile_id)

    async def auction_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id: int = update.effective_chat.id
        user_id: int = update.effective_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output, maybe_bid = game.auction(user_id)
        if len(output.out) > 0:
            await reply(update, output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)
        if maybe_bid is None:
            return
        bid_time_sec: int = maybe_bid
        db.auction_game(self.db_conn, chat_id, user_id, bid_time_sec)

    async def bid_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if context.args is None or len(context.args) < 1:
            await reply(update, "Enter a bid as integer")
            return
        try:
            price: int = int(context.args[0])
        except ValueError:
            await reply(update, "Enter a bid as integer")
            return

        chat_id: int = update.effective_chat.id
        user_id: int = update.effective_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output, maybe_bid = game.bid(user_id, price)
        if len(output.out) > 0:
            await reply(update, output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)
        if maybe_bid is None:
            return
        bid_time_sec: int = maybe_bid
        db.bid_game(self.db_conn, chat_id, user_id, bid_time_sec, price)

    async def rent_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id: int = update.effective_chat.id
        user_id: int = update.effective_user.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        output, maybe_rent = game.rent(user_id)
        if len(output.out) > 0:
            await reply(update, output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)
        if maybe_rent is None:
            return
        caller_money, rentee_id, rentee_money = maybe_rent
        db.rent_chat(
            self.db_conn, chat_id, user_id, caller_money, rentee_id, rentee_money
        )

    async def trade_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id: int = update.effective_chat.id
        _user_id: int = update.effective_user.id
        self.db_sync(chat_id)
        # TODO

    async def finish_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id: int = update.effective_chat.id
        self.db_sync(chat_id)

        maybe_ready = self.ready.pop(chat_id, None)
        maybe_game = self.games.pop(chat_id, None)

        if maybe_game or maybe_ready:
            # Don't make request if there's nothing to delete
            db.finish_game(self.db_conn, chat_id)
        await reply(update, "Stopping")

    async def status_command(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id: int = update.effective_chat.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            await reply(update, "No game in progess")
            return

        user_id: int = update.effective_user.id
        await reply(update, game.get_status(user_id))

    async def map_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        # await upload_photo(update, context)
        chat_id: int = update.effective_chat.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)

        if game is None:
            # Send empty map
            await update.effective_chat.send_photo(MAPS[101])
            return
        # Send map with position of the caller
        user_id: int = update.effective_user.id
        position: int = game.get_position(user_id)
        await update.effective_chat.send_photo(MAPS[position])

    async def build_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if context.args is None or len(context.args) < 1:
            await reply(update, "Enter a position as integer")
            return
        try:
            tile_id: int = int(context.args[0])
        except ValueError:
            await reply(update, "Enter a position as integer")
            return
        
        chat_id: int = update.effective_chat.id
        self.db_sync(chat_id)

        game: Optional[Game] = self.games.get(chat_id, None)
        if game is None:
            return

        user_id: int = update.effective_user.id
        output, maybe_money = game.build(user_id, tile_id)
        if len(output.out) > 0:
            await reply(update, output.out)
        if len(output.warning) > 0:
            warnings.warn(output.warning)
        if maybe_money is None:
            return
        money: int = maybe_money
        db.build_player(self.db_conn, chat_id, user_id, money, tile_id)

    async def query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        elif command == "12":
            await self.map_command(update, context)
        elif command == "13":
            await self.build_command(update, context)
        # else should be unreachable

        await query.answer()
