# -*- coding: utf-8 -*-
"""SQLite: клиенты, услуги, сессии, пополнения."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from avtomoyka_v2.app_settings import get_db_path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT UNIQUE NOT NULL,
    name TEXT,
    balance_rub INTEGER NOT NULL DEFAULT 0,
    bonus_rub INTEGER NOT NULL DEFAULT 0,
    is_blocked INTEGER NOT NULL DEFAULT 0,
    pin_code TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    seconds_total INTEGER NOT NULL,
    seconds_remaining INTEGER NOT NULL,
    active_service_code TEXT,
    started_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS topups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    session_id INTEGER,
    amount_rub INTEGER NOT NULL,
    payment_method TEXT NOT NULL DEFAULT 'card',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
"""

_DEFAULT_SERVICES = [
    ("water", "Вода", 1),
    ("foam", "Пена", 2),
    ("osmos", "Осмос", 3),
    ("wax", "Воск", 4),
    ("vacuum", "Пылесос", 5),
]


def init_db() -> Path:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(_SCHEMA)
        count = conn.execute("SELECT COUNT(*) FROM services").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO services (code, name, sort_order) VALUES (?, ?, ?)",
                _DEFAULT_SERVICES,
            )
        _migrate(conn)
        conn.commit()
    return path


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(clients)").fetchall()}
    if "pin_code" not in cols:
        conn.execute("ALTER TABLE clients ADD COLUMN pin_code TEXT")


@contextmanager
def get_connection():
    init_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
