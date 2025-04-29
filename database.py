import sqlite3
import sys

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


def execute_insert(query: str, params: tuple) -> None:
    try:
        with sqlite3.connect(db_file) as con:
            cur = con.cursor()
            cur.execute(query, params)

            con.commit()
    except Exception as e:
        print("db initialization failed", file=sys.stderr)
        print(e, file=sys.stderr)
