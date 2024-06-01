import psycopg
from psycopg import Connection, sql
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
    result = (row[0], *row[1])
    assert isinstance(result[0], int)
    assert result[1] is None or isinstance(result[1], str)
    assert isinstance(result[2], dict)
    assert isinstance(result[3], int)
    assert isinstance(result[4], int)
    return result


def collect_players(
    rows: list[dict],
) -> list[tuple[int, Optional[str], dict[int, int], int, int]]:
    players: dict[int, tuple[Optional[str], dict[int, int], int, int]] = dict()
    for row in rows:
        user_id: int = row["user_id"]
        is_jailed: bool = row["is_jailed"]
        # Option -> case when player is registerd but owns nothing
        tile_id: Optional[int] = row["tile_id"]
        house_count: Optional[int] = row["house_count"]

        if user_id not in players.keys():
            username: Optional[str] = row["username"]

            ownership: dict[int, int] = (
                {tile_id: house_count} if tile_id is not None else dict()
            )

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
    biggest_bid: int = rows[0]["biggest_bid"]
    bid_time_sec: int = rows[0]["bid_time_sec"]
    bidder_id: int = rows[0]["bidder_id"]
    players: list[tuple[int, Optional[str], dict[int, int], int, int]] = (
        collect_players(rows)
    )
    ser_game = SerGame(
        current_player, status, players, biggest_bid, bid_time_sec, bidder_id
    )
    game, maybe_auction = Game.deserialize(ser_game)
    if maybe_auction is None:
        return game
    # sync with db if auction ended
    money, tile_id = maybe_auction
    buy_user(conn, chat_id, bidder_id, money, tile_id)
    return game


def add_user(
    conn: Connection, chat_id: int, user_id: int, username: Optional[str]
) -> None:
    query: sql.Composed = sql.SQL("""DO $$
BEGIN
    INSERT INTO chat  (chat_id, user_id, "position", money) 
    VALUES ({chat_id}, {user_id}, {position}, {money})
    ON CONFLICT DO NOTHING;

    INSERT INTO meta (user_id, username)
    VALUES ({user_id}, {username})
    ON CONFLICT DO NOTHING;
END $$;""").format(
        chat_id=chat_id,
        user_id=user_id,
        position=-1,
        money=-1,
        username=username,
    )
    conn.execute(query)
    conn.commit()


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
    conn.commit()


def roll_user(
    conn: Connection,
    chat_id: int,
    user_id: int,
    position: int,
    money: int,
    status: str,
) -> None:
    # Have to do it inline because status is a string
    query: sql.Composed = sql.SQL("""DO $$
DECLARE 
    status_0 varchar(10) := {status};
BEGIN
    UPDATE chat SET "position" = {position}, money = {money}
    WHERE player_id = (
        SELECT player_id FROM chat
        WHERE user_id = {user_id} AND chat_id = {chat_id}
    );

    UPDATE game SET status = status_0
    WHERE chat_id = {chat_id};
END $$;""").format(
        status=status,
        position=position,
        money=money,
        user_id=user_id,
        chat_id=chat_id,
    )
    conn.execute(query)
    conn.commit()


def buy_user(
    conn: Connection, chat_id: int, user_id: int, money: int, tile_id: int
) -> None:
    query: sql.Composed = sql.SQL("""DO $$
DECLARE
    player_0 integer;
BEGIN
    player_0 := (
        SELECT player_id FROM chat
        WHERE user_id = {user_id} AND chat_id = {chat_id}
    );

    UPDATE chat SET money = {money}
    WHERE player_id = player_0;

    UPDATE game SET status = 'roll'
    WHERE chat_id = {chat_id};

    INSERT INTO player (player_id, tile_id, house_count)
    VALUES (player_0, {tile_id}, 0);
END $$;""").format(money=money, chat_id=chat_id, user_id=user_id, tile_id=tile_id)

    conn.execute(query)
    conn.commit()


def finish_game(conn: Connection, chat_id: int) -> None:
    query: sql.Composed = sql.SQL("""DO $$
BEGIN
    DELETE FROM game WHERE chat_id = {chat_id};

    DELETE FROM player USING chat 
	WHERE player.player_id = chat.player_id AND chat.chat_id = {chat_id};

	DELETE FROM chat WHERE chat_id = {chat_id};
END $$;""").format(chat_id=chat_id)

    conn.execute(query)
    conn.commit()


def auction_game(
    conn: Connection, chat_id: int, user_id: int, bid_time_sec: int
) -> None:
    query: sql.Composed = sql.SQL(
        """
UPDATE game 
SET 
    status = 'auction', 
    biggest_bid = 40, 
    bid_time_sec = {bid_time_sec}, 
    bidder_id = {user_id}
WHERE chat_id = {chat_id};
"""
    ).format(bid_time_sec=bid_time_sec, user_id=user_id, chat_id=chat_id)

    conn.execute(query)
    conn.commit()


def bid_game(
    conn: Connection, chat_id: int, user_id: int, bid_time_sec: int, price: int
) -> None:
    query: sql.Composed = sql.SQL(
        """
    UPDATE game
    SET
        biggest_bid = {price},
        bid_time_sec = {bid_time_sec},
        bidder_id = {user_id}
    WHERE chat_id = {chat_id};
"""
    ).format(price=price, bid_time_sec=bid_time_sec, user_id=user_id, chat_id=chat_id)

    conn.execute(query)
    conn.commit()


def rent_chat(
    conn: Connection,
    chat_id: int,
    caller_id: int,
    caller_money: int,
    rentee_id: int,
    rentee_money: int,
) -> None:
    query: sql.Composed = sql.SQL(
        """DO $$
    BEGIN
        UPDATE chat
        SET money = {caller_money}
        WHERE chat_id = {chat_id} AND user_id = {caller_id};

        UPDATE chat
        SET money = {rentee_money}
        WHERE chat_id = {chat_id} AND user_id = {rentee_id};
    END $$;"""
    ).format(
        caller_money=caller_money,
        chat_id=chat_id,
        caller_id=caller_id,
        rentee_money=rentee_money,
        rentee_id=rentee_id,
    )

    conn.execute(query)
    conn.commit()


def build_player(
    conn: Connection,
    chat_id: int,
    user_id: int,
    money: int,
    tile_id: int,
) -> None:
    query: sql.Composed = sql.SQL(
        """DO $$
DECLARE
    player_0 integer;
    ownership_0 integer;
BEGIN
    player_0 := (
        SELECT player_id FROM chat WHERE chat_id = {chat_id} AND user_id = {user_id}
    );
    ownership_0 := (
        SELECT id FROM player WHERE player_id = player_0 AND tile_id = {tile_id}
    );
    
    UPDATE chat 
    SET money = {money}
    WHERE player_id = player_0;

    UPDATE player
    SET house_count = house_count + 1
    WHERE id = ownership_0;
END $$;"""
    ).format(chat_id=chat_id, user_id=user_id, tile_id=tile_id, money=money)

    conn.execute(query)
    conn.commit()
