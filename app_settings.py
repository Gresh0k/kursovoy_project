# -*- coding: utf-8 -*-
"""Настройки приложения постамата v1.1."""

import configparser
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_CONFIG_PATH = _ROOT / "config.ini"


def _load() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read(_CONFIG_PATH, encoding="utf-8")
    return cfg


def get_version() -> str:
    return _load().get("app", "version", fallback="1.1")


def admin_panel_enabled() -> bool:
    return get_version() >= "1.1"


def get_db_path() -> Path:
    raw = _load().get("database", "path", fallback="avto_v2.db")
    p = Path(raw)
    return p if p.is_absolute() else _ROOT / p


def is_fullscreen() -> bool:
    return _load().getboolean("kiosk", "fullscreen", fallback=True)


def idle_timeout_seconds() -> int:
    """Бездействие на экранах ввода — возврат на главную."""
    return _load().getint("kiosk", "idle_timeout_seconds", fallback=60)


def rub_per_second() -> int:
    return _load().getint("tariff", "rub_per_second", fallback=1)


def pause_budget_seconds() -> int:
    return _load().getint("tariff", "pause_budget_seconds", fallback=60)


def session_warning_seconds() -> int:
    """За сколько секунд до конца включить мигание таймера."""
    return _load().getint("tariff", "session_warning_seconds", fallback=30)


def admin_phone() -> str:
    return _load().get("auth", "admin_phone", fallback="88005553535").strip()


def admin_pin() -> str:
    return _load().get("auth", "admin_pin", fallback="2026").strip()


def pin_length() -> int:
    return _load().getint("auth", "pin_length", fallback=4)
