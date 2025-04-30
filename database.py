import sqlite3
import sys

db_file = "secret_sharing_is_caring.db"


def init_db() -> None:
    """
    create the database file and table if it does not exist yet
    """
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
    """
    insert user with optional values in the database

    params:
        username: str,
        client_id: Opt<str>,
        client_secret: Opt<str>,
        curr_device: Opt<str>,
    returns:
        None
    """
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
    """
    update values for a user in the database

    params:
        username: str,
        client_id: Opt<str>,
        client_secret: Opt<str>,
        curr_device: Opt<str>,
    returns:
        None
    """
    # username | client_id | client_secret | curr_device
    try:
        user_data = get_db_users(username)
    except Exception as e:
        print(f"error when search user in database: {e}")
        return

    if user_data == []:
        raise ValueError("failed to update user data in db")

    user_data = user_data[0]

    new_data = (
        client_id or user_data[1],
        client_secret or user_data[2],
        curr_device or user_data[3],
        username,
    )

    query = """
        UPDATE users
        SET
        client_id = ?, client_secret = ?, current_device = ?
        WHERE
        id = ?
    """
    try:
        with sqlite3.connect(db_file) as con:
            cur = con.cursor()
            cur.execute(query, new_data)

            con.commit()
    except Exception as e:
        print(e, file=sys.stderr)
        raise ValueError("db insertion failed")


def get_db_users(username: str | None = None) -> list[tuple[str, str, str, str]]:
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
        print(e, file=sys.stderr)
        raise ValueError("db selection failed")
