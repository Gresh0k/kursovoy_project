# -*- coding: utf-8 -*-
"""Подтверждение входа: PIN-код и служебный доступ."""

from avtomoyka_v2.app_settings import admin_phone, admin_pin, pin_length
from avtomoyka_v2.services.client_service import get_client_pin, verify_client_pin


def normalize_phone(phone: str) -> str:
    return phone.strip()


def is_admin_phone(phone: str) -> bool:
    return normalize_phone(phone) == admin_phone()


def verify_admin_pin(pin: str) -> bool:
    return pin == admin_pin()


def get_pin_length() -> int:
    return pin_length()


def client_needs_pin_setup(client_id: int) -> bool:
    return get_client_pin(client_id) is None


def verify_client_login(client_id: int, pin: str) -> bool:
    return verify_client_pin(client_id, pin)
