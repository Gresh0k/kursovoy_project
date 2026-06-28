# -*- coding: utf-8 -*-
"""Экран окончания сессии."""

import tkinter as tk

from avtomoyka_v2.ui import styles as S
from avtomoyka_v2.ui.widgets import touch_button


class FinishScreen(tk.Frame):
    def __init__(self, master, app, seconds_used: int, seconds_total: int, bonus_refund: int = 0):
        super().__init__(master, bg=S.BG)
        self.app = app

        tk.Label(self, text="Мойка завершена", font=S.FONT_TITLE, bg=S.BG, fg=S.FG).pack(pady=(80, 16))
        tk.Label(
            self,
            text=f"Использовано: {seconds_used} сек из {seconds_total} сек",
            font=S.FONT_HEAD,
            bg=S.BG,
            fg=S.MUTED,
            justify="center",
        ).pack(pady=8)

        if bonus_refund > 0:
            tk.Label(
                self,
                text=(
                    f"Неиспользованное время: {bonus_refund} сек\n"
                    f"Зачислено на бонусный счёт: {bonus_refund} ₽"
                ),
                font=S.FONT_HEAD,
                bg=S.BG,
                fg=S.SUCCESS,
                justify="center",
            ).pack(pady=12)

        tk.Label(self, text="Спасибо! Хорошей дороги!", font=S.FONT_BODY, bg=S.BG, fg=S.FG).pack(pady=8)

        touch_button(self, "На главный экран", app.show_welcome, bg=S.ACCENT, width=18).pack(pady=40)

        self._countdown = 15
        self.hint = tk.Label(
            self,
            text=f"Автоматический возврат через {self._countdown} сек",
            font=S.FONT_BODY,
            bg=S.BG,
            fg=S.MUTED,
        )
        self.hint.pack()
        self._auto_return()

    def _auto_return(self):
        self._countdown -= 1
        if self._countdown <= 0:
            self.app.show_welcome()
            return
        self.hint.config(text=f"Автоматический возврат через {self._countdown} сек")
        self.after(1000, self._auto_return)
