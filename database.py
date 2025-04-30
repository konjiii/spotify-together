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


def insert_db_user(
    username: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    curr_device: str | None = None,
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
        print(e, file=sys.stderr)
        raise ValueError("db insertion failed")


def update_db_user(
    username: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    curr_device: str | None = None,
) -> None:
    # username | client_id | client_secret | curr_device
    user_data = get_db_users(username)

    if user_data is None:
        raise ValueError("failed to update user data in db")

    new_data = (
        username,
        client_id or user_data[1],
        client_id or user_data[2],
        curr_device or user_data[3],
    )

    query = """
        INSERT INTO users
        (id, client_id, client_secret, current_device)
        VALUES
        (?, ?, ?, ?)
    """
    try:
        with sqlite3.connect(db_file) as con:
            cur = con.cursor()
            cur.execute(query, new_data)

            con.commit()
    except Exception as e:
        print(e, file=sys.stderr)
        raise ValueError("db insertion failed")


def get_db_users(username: str | None = None) -> list[tuple[str, str, str, str]] | None:
    """
    get user data from the database and return it as a list of users
    when username is given, returns data of single user else returns all users

    params:
        username: Opt<str>
    returns:
        list[tuple[username, client_id, client_secret, curr_dev]]
    """

    if username is None:
        query = "SELECT * FROM users"
    else:
        query = f"SELECT * FROM users WHERE id='{username}'"

    try:
        with sqlite3.connect(db_file) as con:
            cur = con.cursor()
            res = cur.execute(query)

            return res.fetchall()
    except Exception as e:
        print("db selection failed", file=sys.stderr)
        print(e, file=sys.stderr)
