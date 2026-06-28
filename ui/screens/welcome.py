# -*- coding: utf-8 -*-
"""Стартовый экран."""

import tkinter as tk

from avtomoyka_v2.ui import styles as S
from avtomoyka_v2.ui.widgets import touch_button


class WelcomeScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=S.BG)
        self.app = app

        tk.Label(self, text="Автомойка самообслуживания", font=S.FONT_TITLE, bg=S.BG, fg=S.FG).pack(
            pady=(80, 10)
        )
        tk.Label(
            self,
            text="1 рубль = 1 секунда мойки\nВы сами выбираете: вода, пена, осмос и др.",
            font=S.FONT_BODY,
            bg=S.BG,
            fg=S.MUTED,
            justify="center",
        ).pack(pady=(0, 60))

        btn_frame = tk.Frame(self, bg=S.BG)
        btn_frame.pack(expand=True)

        touch_button(
            btn_frame,
            "Пополнить и начать",
            lambda: app.show_topup(),
            width=S.BTN_MIN_WIDTH,
        ).pack(pady=12)

        touch_button(
            btn_frame,
            "Я зарегистрирован\n(вход по телефону)",
            app.show_phone,
            bg=S.BG_CARD,
            width=S.BTN_MIN_WIDTH,
        ).pack(pady=12)
