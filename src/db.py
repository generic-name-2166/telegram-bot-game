import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from pathlib import Path
from typing import Any, Optional

from secret import load_cloud, load_local
from monopoly import SerGame, Game


PARENT: Path = Path(__file__).resolve(strict=True).parent


def select_sql() -> str:
    with open(PARENT.joinpath("select.sql")) as file:
        query: str = file.read()
    return query


def connect_to_db(context: Any) -> Connection:
    # God knows what this context is

    secrets: Path = PARENT.joinpath("secret.txt")
    if secrets.is_file():
        # Running locally
        params: dict = load_local()
    else:
        # Running in the cloud
        params: dict = load_cloud(context)

    conn: Connection = psycopg.connect(row_factory=dict_row, **params)
    return conn


def flatten_row(
    row: tuple[int, tuple[Optional[str], dict[int, int], int, int]],
) -> tuple[int, Optional[str], dict[int, int], int, int]:
    return (row[0], *row[1])


def collect_players(
    rows: list[dict],
) -> list[tuple[int, Optional[str], dict[int, int], int, int]]:
    players: dict[int, tuple[Optional[str], dict[int, int], int, int]] = dict()
    for row in rows:
        user_id: int = row["user_id"]
        tile_id: int = row["tile_id"]
        house_count: int = row["house_count"]

        if user_id not in players.keys():
            username: Optional[str] = row["username"]
            ownership: dict[int, int] = {tile_id: house_count}
            position: int = row["position"]
            money: int = row["money"]
            players[user_id] = (username, ownership, position, money)
        else:
            players[user_id][1][tile_id] = house_count

    # From Python 3.6 `dict` preserves inserion order
    # That is, the order that was in Postgres
    return list(map(flatten_row, players.items()))


def fetch_game(
    conn: Connection, chat_id: int
) -> None | list[tuple[int, Optional[str]]] | Game:
    query: str = select_sql()
    params: tuple[int] = (chat_id,)
    rows: list[dict] = conn.execute(query, params).fetchall()

    if len(rows) == 0:
        # Game not ready
        return None
    elif rows[0]["status"] is None:
        # Game not ready but there are ready players
        return [(row["user_id"], row["username"]) for row in rows]

    # Game in progress
    current_player: int = rows[0]["current_player"]
    status: str = rows[0]["status"]
    players: list[tuple[int, Optional[str], dict[int, int], int, int]] = (
        collect_players(rows)
    )
    ser_game = SerGame(current_player, status, players)
    return Game.deserialize(ser_game)


def start_user_sql() -> str:
    with open(PARENT.joinpath("start_user.sql")) as file:
        query: str = file.read()
    return query


def add_user(
    conn: Connection, chat_id: int, user_id: int, username: Optional[str]
) -> None:
    params = {
        "chat_id": chat_id,
        "user_id": user_id,
        "position": -1,
        "money": -1,
        "username": username,
    }
    conn.execute(start_user_sql(), params)


def begin_game_sql() -> str:
    with open(PARENT.joinpath("begin_game.sql")) as file:
        query: str = file.read()
    return query


def begin_user_sql() -> str:
    with open(PARENT.joinpath("begin_user.sql")) as file:
        query: str = file.read()
    return query


def begin_game(conn: Connection, chat_id: int, ready_ids: tuple[int]) -> None:
    cursor = conn.execute(
        begin_game_sql(),
        (chat_id,),
    )

    query = begin_user_sql()

    for user_id in ready_ids:
        cursor.execute(
            query,
            {
                "chat_id": chat_id,
                "user_id": user_id,
            },
        )


def roll_user_sql() -> str:
    with open(PARENT.joinpath("roll_user.sql")) as file:
        query: str = file.read()
    return query


def roll_user(
    conn: Connection, chat_id: int, user_id: int, position: int, money: int
) -> None:
    conn.execute(
        roll_user_sql(),
        {
            "position": position,
            "money": money,
            "chat_id": chat_id,
            "user_id": user_id,
        },
    )


def buy_user_sql() -> str:
    with open(PARENT.joinpath("buy_user.sql")) as file:
        query: str = file.read()
    return query


def buy_user(conn: Connection, chat_id: int, user_id: int, money: int) -> None:
    conn.execute(
        buy_user_sql(),
        {
            "money": money,
            "chat_id": chat_id,
            "user_id": user_id,
        },
    )
