# -*- coding: utf-8 -*-
"""Клиенты: регистрация, баланс, блокировка."""

from dataclasses import dataclass
from typing import List, Optional

from avtomoyka_v2.data.db import get_connection


@dataclass
class Client:
    id: int
    phone: str
    name: Optional[str]
    balance_rub: int
    bonus_rub: int
    is_blocked: bool


def _row_to_client(row) -> Client:
    return Client(
        id=row["id"],
        phone=row["phone"],
        name=row["name"],
        balance_rub=row["balance_rub"],
        bonus_rub=row["bonus_rub"],
        is_blocked=bool(row["is_blocked"]),
    )


def get_client(client_id: int) -> Optional[Client]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    return _row_to_client(row) if row else None


def find_by_phone(phone: str) -> Optional[Client]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE phone = ?",
            (phone,),
        ).fetchone()
    return _row_to_client(row) if row else None


def register(phone: str, name: str = "") -> Client:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clients (phone, name) VALUES (?, ?)",
            (phone, name or None),
        )
        row = conn.execute(
            "SELECT * FROM clients WHERE phone = ?",
            (phone,),
        ).fetchone()
    return _row_to_client(row)


def add_balance(client_id: int, amount_rub: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE clients SET balance_rub = balance_rub + ? WHERE id = ?",
            (amount_rub, client_id),
        )
        conn.execute(
            "INSERT INTO topups (client_id, amount_rub) VALUES (?, ?)",
            (client_id, amount_rub),
        )


def deduct_bonus(client_id: int, amount: int) -> bool:
    if amount <= 0:
        return True
    with get_connection() as conn:
        row = conn.execute(
            "SELECT bonus_rub FROM clients WHERE id = ?",
            (client_id,),
        ).fetchone()
        if not row or row["bonus_rub"] < amount:
            return False
        conn.execute(
            "UPDATE clients SET bonus_rub = bonus_rub - ? WHERE id = ?",
            (amount, client_id),
        )
    return True


def add_bonus(client_id: int, amount: int) -> None:
    if amount <= 0:
        return
    with get_connection() as conn:
        conn.execute(
            "UPDATE clients SET bonus_rub = bonus_rub + ? WHERE id = ?",
            (amount, client_id),
        )


def spend_bonuses(client_id: int, bonus_spent: int) -> None:
    """Списать бонусы при оплате мойки."""
    if bonus_spent <= 0:
        return
    if not deduct_bonus(client_id, bonus_spent):
        raise ValueError("Недостаточно бонусных баллов")


def deduct_balance(client_id: int, amount_rub: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT balance_rub FROM clients WHERE id = ?",
            (client_id,),
        ).fetchone()
        if not row or row["balance_rub"] < amount_rub:
            return False
        conn.execute(
            "UPDATE clients SET balance_rub = balance_rub - ? WHERE id = ?",
            (amount_rub, client_id),
        )
    return True


def get_client_pin(client_id: int) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT pin_code FROM clients WHERE id = ?",
            (client_id,),
        ).fetchone()
    if not row or not row["pin_code"]:
        return None
    return str(row["pin_code"])


def set_client_pin(client_id: int, pin: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE clients SET pin_code = ? WHERE id = ?",
            (pin, client_id),
        )


def verify_client_pin(client_id: int, pin: str) -> bool:
    stored = get_client_pin(client_id)
    return stored is not None and stored == pin


def list_clients() -> List[Client]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM clients ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_client(r) for r in rows]


def set_blocked(client_id: int, blocked: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE clients SET is_blocked = ? WHERE id = ?",
            (1 if blocked else 0, client_id),
        )


def set_bonus(client_id: int, bonus_rub: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE clients SET bonus_rub = ? WHERE id = ?",
            (max(0, bonus_rub), client_id),
        )
