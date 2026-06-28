# -*- coding: utf-8 -*-
"""Вход по телефону для зарегистрированных клиентов."""

import tkinter as tk

from avtomoyka.services.client_service import find_by_phone, register
from avtomoyka.ui import styles as S
from avtomoyka.ui.dialogs import ask_yes_no, show_error, show_warning
from avtomoyka.ui.widgets import Numpad, touch_button


class PhoneScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=S.BG)
        self.app = app

        bottom = tk.Frame(self, bg=S.BG)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=12, padx=8)
        row = tk.Frame(bottom, bg=S.BG)
        row.pack(fill=tk.X)
        touch_button(row, "Продолжить", self._continue, bg=S.ACCENT).pack(
            side=tk.LEFT, padx=4, expand=True, fill=tk.X
        )
        touch_button(row, "Назад", app.show_welcome, bg=S.BG_CARD).pack(
            side=tk.LEFT, padx=4, expand=True, fill=tk.X
        )

        content = tk.Frame(self, bg=S.BG)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tk.Label(content, text="Вход по телефону", font=S.FONT_TITLE, bg=S.BG, fg=S.FG).pack(
            pady=(24, 8)
        )
        tk.Label(content, text="Введите номер телефона", font=S.FONT_BODY, bg=S.BG, fg=S.MUTED).pack(
            pady=8
        )

        self.numpad = Numpad(content, lambda _v: None, max_len=11)
        self.numpad.pack(pady=8)

    def _continue(self):
        phone = self.numpad.value.strip()
        if len(phone) < 10:
            show_warning(
                self,
                "Телефон",
                "Введите корректный номер (10–11 цифр)",
            )
            return

        client = find_by_phone(phone)
        if client is None:
            ask_yes_no(
                self,
                "Регистрация",
                f"Клиент {phone} не найден.\nЗарегистрировать?",
                on_yes=lambda: self._finish_login(register(phone)),
            )
            return

        self._finish_login(client)

    def _finish_login(self, client):
        if client.is_blocked:
            show_error(
                self,
                "Доступ закрыт",
                "Аккаунт заблокирован.\nОбратитесь к администратору.",
            )
            return

        self.app.show_topup(client)
