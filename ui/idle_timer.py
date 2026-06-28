# -*- coding: utf-8 -*-
"""Таймаут бездействия — возврат на главный экран."""

import tkinter as tk
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from avtomoyka.ui.kiosk_app import KioskApp


class IdleTimer:
    def __init__(self, root: tk.Tk, app: "KioskApp"):
        self.root = root
        self.app = app
        self._timeout_sec = 0
        self._job: Optional[str] = None
        root.bind_all("<Button-1>", self._on_activity, add="+")
        root.bind_all("<Key>", self._on_activity, add="+")

    def arm(self, timeout_sec: int) -> None:
        self._timeout_sec = max(0, timeout_sec)
        self._reset()

    def disarm(self) -> None:
        self._timeout_sec = 0
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None

    def _on_activity(self, _event=None) -> None:
        if self._timeout_sec > 0:
            self._reset()

    def _reset(self) -> None:
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        if self._timeout_sec <= 0:
            return
        self._job = self.root.after(self._timeout_sec * 1000, self._expire)

    def _expire(self) -> None:
        self._job = None
        self._timeout_sec = 0
        self.app.show_welcome()
