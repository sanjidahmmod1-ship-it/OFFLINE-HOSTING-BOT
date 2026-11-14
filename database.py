import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bots.db"

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=20)
    db.execute("PRAGMA foreign_keys = ON")
    return db

def init_db():
    with connect() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            banned INTEGER NOT NULL DEFAULT 0
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            telegram_id INTEGER NOT NULL UNIQUE,
            username TEXT NOT NULL,
            first_name TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(owner_id) REFERENCES users(user_id)
        )
        """)

def save_user(user_id):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))

def add_bot(owner_id, telegram_id, username, first_name, encrypted_token):
    try:
        with connect() as db:
            db.execute(
                """INSERT INTO bots(owner_id, telegram_id, username, first_name, token)
                   VALUES(?, ?, ?, ?, ?)""",
                (owner_id, telegram_id, username, first_name, encrypted_token)
            )
        return True
    except sqlite3.IntegrityError:
        return False

def get_bots(owner_id):
    with connect() as db:
        return db.execute(
            "SELECT id, username, first_name FROM bots WHERE owner_id=? ORDER BY id DESC",
            (owner_id,)
        ).fetchall()

def get_bot(row_id, owner_id):
    with connect() as db:
        return db.execute(
            """SELECT id, telegram_id, username, first_name, token
               FROM bots WHERE id=? AND owner_id=?""",
            (row_id, owner_id)
        ).fetchone()

def delete_bot(row_id, owner_id):
    with connect() as db:
        cur = db.execute("DELETE FROM bots WHERE id=? AND owner_id=?", (row_id, owner_id))
        return cur.rowcount > 0

def stats():
    with connect() as db:
        users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        bots = db.execute("SELECT COUNT(*) FROM bots").fetchone()[0]
        return users, bots

def is_banned(user_id):
    with connect() as db:
        row = db.execute("SELECT banned FROM users WHERE user_id=?", (user_id,)).fetchone()
        return bool(row and row[0])

def set_ban(user_id, status):
    with connect() as db:
        db.execute(
            """INSERT INTO users(user_id, banned) VALUES(?, ?)
               ON CONFLICT(user_id) DO UPDATE SET banned=excluded.banned""",
            (user_id, int(status))
        )

def all_users():
    with connect() as db:
        return [r[0] for r in db.execute("SELECT user_id FROM users").fetchall()]
