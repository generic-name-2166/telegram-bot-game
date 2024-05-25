import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from pathlib import Path
from typing import Any

from secret import load_cloud, load_local


def connect_to_db(context: Any) -> Connection:
    # God knows what this context is

    secrets: Path = Path("./secret.txt")
    if secrets.is_file():
        # Running locally
        params: dict = load_local()
    else:
        # Running in the cloud
        params: dict = load_cloud(context)

    conn: Connection = psycopg.connect(row_factory=dict_row, **params)
    return conn
