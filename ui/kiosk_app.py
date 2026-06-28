# -*- coding: utf-8 -*-
"""Главное окно постамата v1.0."""

import tkinter as tk
from typing import Optional

from avtomoyka.app_settings import get_version, idle_timeout_seconds, is_fullscreen
from avtomoyka.data.db import init_db
from avtomoyka.services.client_service import Client
from avtomoyka.ui import styles as S
from avtomoyka.ui.idle_timer import IdleTimer
from avtomoyka.ui.screens.finish import FinishScreen
from avtomoyka.ui.screens.phone import PhoneScreen
from avtomoyka.ui.screens.session import SessionScreen
from avtomoyka.ui.screens.topup import TopUpScreen
from avtomoyka.ui.screens.welcome import WelcomeScreen


class KioskApp:
    def __init__(self):
        init_db()
        self.root = tk.Tk()
        self.root.title(f"АвтоМойка — пост {get_version()}")
        self.root.configure(bg=S.BG)
        self.root.geometry("1024x768")
        if is_fullscreen():
            self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda _e: self.root.attributes("-fullscreen", False))

        self._container = tk.Frame(self.root, bg=S.BG)
        self._container.pack(fill="both", expand=True)

        self._current: Optional[tk.Frame] = None
        self._client: Optional[Client] = None
        self._idle = IdleTimer(self.root, self)

        self.show_welcome()

    def _clear(self):
        if self._current:
            self._current.destroy()
            self._current = None
        self._idle.disarm()

    def _show(self, frame: tk.Frame, *, use_idle: bool = False):
        self._clear()
        self._current = frame
        self._current.pack(fill="both", expand=True)
        if use_idle:
            self._idle.arm(idle_timeout_seconds())

    def show_welcome(self):
        self._client = None
        self._show(WelcomeScreen(self._container, self))

    def show_topup(self, client: Optional[Client] = None, use_balance_only: bool = False):
        self._client = client
        self._show(TopUpScreen(self._container, self, client, use_balance_only), use_idle=True)

    def show_phone(self):
        self._show(PhoneScreen(self._container, self), use_idle=True)

    def start_session(self, seconds: int, client: Optional[Client] = None):
        self._show(SessionScreen(self._container, self, seconds, client))

    def show_finish(self, seconds_used: int, seconds_total: int, bonus_refund: int = 0):
        self._show(
            FinishScreen(self._container, self, seconds_used, seconds_total, bonus_refund)
        )

    def run(self):
        self.root.mainloop()
