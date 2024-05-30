import os
import asyncio
from psycopg import Connection

from monopoly import SerGame, Game
from index import handler
from db import connect_to_db, fetch_game


async def test_handler() -> None:
    with open("secret.txt") as F:
        start = F.readline().strip()
        begin = F.readline().strip()
        roll = F.readline().strip()
        bot_token = F.readline().strip()

    os.environ["BOT_TOKEN"] = bot_token

    start_msg = {
        "messages": [
            {
                "details": {
                    "message": {
                        "body": start,
                    }
                }
            }
        ]
    }
    begin_msg = {
        "messages": [
            {
                "details": {
                    "message": {
                        "body": begin,
                    }
                }
            }
        ]
    }
    roll_msg = {
        "messages": [
            {
                "details": {
                    "message": {
                        "body": roll,
                    }
                }
            }
        ]
    }
    await handler(start_msg, None)
    await handler(begin_msg, None)
    await handler(roll_msg, None)


def test_game() -> None:
    game = Game(((0, "Gaming"),))
    output, _change = game.roll(0)
    print(output.out)
    print(output.warning)


def test_serialize() -> None:
    game = Game(((0, "Gaming"),))
    _output = game.roll(0)
    ser_game: SerGame = game.serialize()
    print(ser_game.current_player)
    print(ser_game.status)
    print(ser_game.players)


def test_db() -> None:
    conn: Connection = connect_to_db(None)
    chat_0: int = 0
    maybe_game_0 = fetch_game(conn, chat_0)
    assert isinstance(maybe_game_0, Game)
    output, _maybe_change = maybe_game_0.roll(0)
    print(output.out)

    chat_1: int = 1
    maybe_game_1 = fetch_game(conn, chat_1)
    assert isinstance(maybe_game_1, list)
    print(maybe_game_1)


if __name__ == "__main__":
    asyncio.run(test_handler())
    test_game()
    test_serialize()
    test_db()
