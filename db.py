"""
Simple SQLite store for per-user Kindle email addresses.
Database file: kindle_users.db (gitignored)
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "kindle_users.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users "
        "(user_id INTEGER PRIMARY KEY, kindle_email TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def get_kindle_email(user_id: int) -> str | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT kindle_email FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row[0] if row else None


def set_kindle_email(user_id: int, kindle_email: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO users (user_id, kindle_email) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET kindle_email = excluded.kindle_email",
            (user_id, kindle_email),
        )
        conn.commit()
