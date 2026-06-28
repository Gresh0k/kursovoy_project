# -*- coding: utf-8 -*-
"""Сессии мойки: таймер, услуги."""

from dataclasses import dataclass
from typing import List, Optional

from avtomoyka_v2.data.db import get_connection


@dataclass
class Service:
    code: str
    name: str


@dataclass
class Session:
    id: int
    client_id: Optional[int]
    seconds_total: int
    seconds_remaining: int
    active_service_code: Optional[str]
    status: str


def list_services() -> List[Service]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT code, name FROM services WHERE is_active = 1 ORDER BY sort_order"
        ).fetchall()
    return [Service(r["code"], r["name"]) for r in rows]


def start_session(seconds: int, client_id: Optional[int] = None, free: bool = False) -> Session:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO sessions (client_id, seconds_total, seconds_remaining, status)
            VALUES (?, ?, ?, 'active')
            """,
            (client_id, seconds, seconds),
        )
        session_id = cur.lastrowid
        if free:
            conn.execute(
                """
                INSERT INTO topups (client_id, session_id, amount_rub, payment_method)
                VALUES (?, ?, 0, 'admin')
                """,
                (client_id, session_id),
            )
        else:
            conn.execute(
                "INSERT INTO topups (client_id, session_id, amount_rub) VALUES (?, ?, ?)",
                (client_id, session_id, seconds),
            )
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return _row_to_session(row)


def get_session(session_id: int) -> Optional[Session]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return _row_to_session(row) if row else None


def set_active_service(session_id: int, service_code: Optional[str]) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET active_service_code = ? WHERE id = ?",
            (service_code, session_id),
        )


def tick_session(session_id: int) -> Optional[Session]:
    """Уменьшить таймер на 1 сек. Возвращает None, если сессия завершена."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ? AND status = 'active'",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        remaining = row["seconds_remaining"] - 1
        if remaining <= 0:
            conn.execute(
                """
                UPDATE sessions
                SET seconds_remaining = 0, status = 'finished',
                    ended_at = datetime('now', 'localtime'), active_service_code = NULL
                WHERE id = ?
                """,
                (session_id,),
            )
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            return _row_to_session(row)
        conn.execute(
            "UPDATE sessions SET seconds_remaining = ? WHERE id = ?",
            (remaining, session_id),
        )
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return _row_to_session(row)


def finish_session(session_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET status = 'finished', ended_at = datetime('now', 'localtime'),
                active_service_code = NULL
            WHERE id = ?
            """,
            (session_id,),
        )


def _row_to_session(row) -> Session:
    return Session(
        id=row["id"],
        client_id=row["client_id"],
        seconds_total=row["seconds_total"],
        seconds_remaining=row["seconds_remaining"],
        active_service_code=row["active_service_code"],
        status=row["status"],
    )
