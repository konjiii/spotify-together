import sqlite3
import sys
from typing import Any

db_file = "secret_sharing_is_caring.db"


def init_db() -> None:
    try:
        with sqlite3.connect(db_file) as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users(
                    id TEXT PRIMARY KEY,
                    client_id TEXT,
                    client_secret TEXT,
                    current_device TEXT
                )
            """)

            con.commit()
    except Exception as e:
        print("db initialization failed", file=sys.stderr)
        print(e, file=sys.stderr)


def insert_db_user(
    username: str, client_id: str, client_secret: str, curr_device: str
) -> None:
    query = """
        INSERT INTO users
        (id, client_id, client_secret, current_device)
        VALUES
        (?, ?, ?, ?)
    """
    try:
        with sqlite3.connect(db_file) as con:
            cur = con.cursor()
            cur.execute(query, (username, client_id, client_secret, curr_device))

            con.commit()
    except Exception as e:
        print("db insertion failed", file=sys.stderr)
        print(e, file=sys.stderr)


def get_db_users() -> list[Any] | None:
    query = "SELECT * FROM users"

    try:
        with sqlite3.connect(db_file) as con:
            cur = con.cursor()
            res = cur.execute(query)

            return res.fetchall()
    except Exception as e:
        print("db selection failed", file=sys.stderr)
        print(e, file=sys.stderr)
