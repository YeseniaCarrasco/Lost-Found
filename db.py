"""SQLite helpers: one connection per request, schema creation, and first-run seeding."""
import os
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    category    TEXT    NOT NULL DEFAULT 'Other',
    location    TEXT    NOT NULL,
    found_date  TEXT    NOT NULL,            -- ISO date, YYYY-MM-DD
    photo_url   TEXT    NOT NULL DEFAULT '',
    status      TEXT    NOT NULL DEFAULT 'unclaimed'
                CHECK (status IN ('unclaimed', 'returned')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    returned_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_user   ON items(user_id);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(path):
    """Create tables if needed and fill an empty database with demo data."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = connect(path)
    try:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            from seed import seed
            seed(conn)
        conn.commit()
    finally:
        conn.close()
