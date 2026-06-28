# -*- coding: utf-8 -*-
"""Ввод PIN-кода: вход клиента, регистрация, служебный доступ."""

import tkinter as tk
from typing import Literal, Optional

from avtomoyka_v2.services.auth_service import (
    client_needs_pin_setup,
    get_pin_length,
    verify_admin_pin,
    verify_client_login,
)
from avtomoyka_v2.services.client_service import Client, get_client, set_client_pin
from avtomoyka_v2.ui import styles as S
from avtomoyka_v2.ui.dialogs import show_error, show_warning
from avtomoyka_v2.ui.widgets import PinPad, touch_button

PinMode = Literal["client_login", "client_setup", "client_setup_confirm", "admin_login"]


class PinScreen(tk.Frame):
    def __init__(
        self,
        master,
        app,
        mode: PinMode,
        phone: str = "",
        client: Optional[Client] = None,
        setup_pin: str = "",
    ):
        super().__init__(master, bg=S.BG)
        self.app = app
        self.mode = mode
        self.phone = phone
        self.client = get_client(client.id) if client else None
        self.setup_pin = setup_pin
        self._pin_len = get_pin_length()

        bottom = tk.Frame(self, bg=S.BG)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=12, padx=8)
        row = tk.Frame(bottom, bg=S.BG)
        row.pack(fill=tk.X)
        touch_button(row, "Продолжить", self._submit, bg=S.ACCENT).pack(
            side=tk.LEFT, padx=4, expand=True, fill=tk.X
        )
        touch_button(row, "Назад", self._back, bg=S.BG_CARD).pack(
            side=tk.LEFT, padx=4, expand=True, fill=tk.X
        )

        content = tk.Frame(self, bg=S.BG)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        title, hint = self._texts()
        tk.Label(content, text=title, font=S.FONT_TITLE, bg=S.BG, fg=S.FG).pack(
            pady=(24, 8)
        )
        if self.phone and self.mode != "admin_login":
            tk.Label(
                content,
                text=f"Телефон: {self.phone}",
                font=S.FONT_BODY,
                bg=S.BG,
                fg=S.SUCCESS,
            ).pack(pady=(0, 6))
        tk.Label(
            content,
            text=hint,
            font=S.FONT_BODY,
            bg=S.BG,
            fg=S.MUTED,
            wraplength=640,
            justify="center",
        ).pack(pady=8)

        self.pinpad = PinPad(content, lambda _v: None, pin_length=self._pin_len)
        self.pinpad.pack(pady=12)

    def _texts(self) -> tuple[str, str]:
        if self.mode == "admin_login":
            return (
                "Служебный доступ",
                f"Введите {self._pin_len}-значный код оператора",
            )
        if self.mode == "client_setup":
            return (
                "Код доступа",
                f"Придумайте код из {self._pin_len} цифр.\n"
                "Это быстрее пароля — как SMS-код, но без ожидания сообщения.",
            )
        if self.mode == "client_setup_confirm":
            return (
                "Повторите код",
                f"Введите те же {self._pin_len} цифры ещё раз",
            )
        return (
            "Подтверждение входа",
            f"Введите ваш {self._pin_len}-значный код доступа",
        )

    def _back(self):
        if self.mode == "client_setup_confirm":
            self.app.show_pin_setup(self.phone, self.client)
        else:
            self.app.show_phone()

    def _submit(self):
        pin = self.pinpad.value
        if len(pin) != self._pin_len:
            show_warning(
                self,
                "Код",
                f"Введите {self._pin_len} цифры",
            )
            return

        if self.mode == "admin_login":
            if verify_admin_pin(pin):
                self.app.show_admin()
            else:
                show_error(self, "Доступ", "Неверный служебный код")
                self.pinpad.clear()
            return

        if not self.client:
            self.app.show_phone()
            return

        if self.mode == "client_setup":
            self.app.show_pin_setup_confirm(self.phone, self.client, pin)
            return

        if self.mode == "client_setup_confirm":
            if pin != self.setup_pin:
                show_error(self, "Код", "Коды не совпали.\nПопробуйте снова.")
                self.app.show_pin_setup(self.phone, self.client)
                return
            set_client_pin(self.client.id, pin)
            self.client = get_client(self.client.id)
            self.app.show_topup(self.client)
            return

        if client_needs_pin_setup(self.client.id):
            self.app.show_pin_setup(self.phone, self.client)
            return

        if verify_client_login(self.client.id, pin):
            self.app.show_topup(self.client)
        else:
            show_error(self, "Вход", "Неверный код доступа")
            self.pinpad.clear()
