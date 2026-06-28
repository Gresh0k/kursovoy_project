# -*- coding: utf-8 -*-
"""Пополнение баланса / выбор суммы."""

import tkinter as tk
from typing import Optional

from avtomoyka_v2.services.client_service import (
    Client,
    deduct_balance,
    get_client,
    spend_bonuses,
)
from avtomoyka_v2.ui import styles as S
from avtomoyka_v2.ui.dialogs import show_error, show_warning
from avtomoyka_v2.ui.widgets import Numpad, touch_button

PRESETS = [100, 200, 300, 500]


class TopUpScreen(tk.Frame):
    def __init__(self, master, app, client: Optional[Client], use_balance_only: bool):
        super().__init__(master, bg=S.BG)
        self.app = app
        self.use_balance_only = use_balance_only
        self.selected = 200
        self.bonus_to_use = 0
        self.input_mode = "amount"
        self._mode_buttons = {}

        if client:
            client = get_client(client.id) or client
        self.client = client

        self.bottom = tk.Frame(self, bg=S.BG)
        self.bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=4, padx=8)

        btn_row = tk.Frame(self.bottom, bg=S.BG)
        btn_row.pack(fill=tk.X)
        btn_font = ("Segoe UI", 16, "bold")
        btn_pad = {"padx": 10, "pady": 8}

        self.pay_btn = touch_button(
            btn_row,
            "Оплатить картой",
            self._pay_card,
            bg=S.ACCENT,
            font=btn_font,
            **btn_pad,
        )
        self.pay_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        touch_button(
            btn_row,
            "Назад",
            app.show_welcome,
            bg=S.BG_CARD,
            font=btn_font,
            **btn_pad,
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))

        content = tk.Frame(self, bg=S.BG)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tk.Label(content, text="Пополнение", font=S.FONT_TITLE, bg=S.BG, fg=S.FG).pack(
            pady=(4, 2)
        )

        if self.client:
            tk.Label(
                content,
                text=f"Клиент: {self.client.phone}  |  Бонусов: {self.client.bonus_rub}",
                font=S.FONT_BODY,
                bg=S.BG,
                fg=S.SUCCESS,
            ).pack(pady=(0, 4))
            tk.Label(
                content,
                text="Бонусы — остаток с прошлой мойки, можно оплатить до 100%",
                font=S.FONT_BODY,
                bg=S.BG,
                fg=S.MUTED,
            ).pack(pady=(0, 6))

        tk.Label(
            content,
            text="1 ₽ = 1 сек  •  1 бонус = 1 ₽",
            font=S.FONT_BODY,
            bg=S.BG,
            fg=S.MUTED,
        ).pack(pady=(0, 6))

        presets = tk.Frame(content, bg=S.BG)
        presets.pack(pady=2)
        for amount in PRESETS:
            touch_button(
                presets,
                f"{amount} ₽",
                lambda a=amount: self._pick(a),
                width=7,
            ).pack(side=tk.LEFT, padx=4)

        if self.client and self.client.balance_rub > 0:
            touch_button(
                presets,
                f"С баланса {self.client.balance_rub} ₽",
                self._pay_from_balance,
                bg=S.SUCCESS,
                width=10,
            ).pack(side=tk.LEFT, padx=4)

        if self.client:
            mode_row = tk.Frame(content, bg=S.BG)
            mode_row.pack(pady=(10, 4))
            tk.Label(mode_row, text="Клавиатура для:", font=S.FONT_BODY, bg=S.BG, fg=S.MUTED).pack(
                side=tk.LEFT, padx=4
            )
            self._mode_buttons["amount"] = touch_button(
                mode_row,
                "Сумма ₽",
                lambda: self._set_mode("amount"),
                bg=S.ACCENT,
                width=10,
            )
            self._mode_buttons["amount"].pack(side=tk.LEFT, padx=4)
            self._mode_buttons["bonus"] = touch_button(
                mode_row,
                "Списать бонусы",
                lambda: self._set_mode("bonus"),
                bg=S.BG_CARD,
                width=12,
            )
            self._mode_buttons["bonus"].pack(side=tk.LEFT, padx=4)

        self.mode_hint = tk.Label(
            content,
            text="Введите сумму пополнения на клавиатуре ниже",
            font=S.FONT_HEAD,
            bg=S.BG,
            fg=S.FG,
            wraplength=700,
            justify="center",
        )
        self.mode_hint.pack(pady=(2, 4))

        input_row = tk.Frame(content, bg=S.BG)
        input_row.pack(pady=2, fill=tk.BOTH, expand=True)
        self._input_row = input_row

        self.numpad = Numpad(input_row, self._on_numpad_change, max_len=4)
        self.numpad.place(relx=0.5, rely=0, anchor=tk.N)

        self._summary_width = 280
        self._numpad_summary_gap = 28
        self._summary_col = tk.Frame(input_row, bg=S.BG, width=self._summary_width)
        self._summary_col.pack_propagate(False)

        self.summary_label = tk.Label(
            self._summary_col,
            text="",
            font=S.FONT_BODY,
            bg=S.BG,
            fg=S.FG,
            justify=tk.LEFT,
            anchor=tk.NW,
            wraplength=self._summary_width,
        )
        self.summary_label.pack(anchor=tk.NW, fill=tk.X)

        input_row.bind("<Configure>", lambda _e: self._layout_numpad_summary())
        self.after_idle(self._layout_numpad_summary)

        self._pick(200)

    def _layout_numpad_summary(self):
        if not hasattr(self, "_input_row") or not hasattr(self, "_summary_col"):
            return
        self.update_idletasks()
        row_w = self._input_row.winfo_width()
        if row_w <= 1:
            return
        np_w = self.numpad.winfo_reqwidth()
        x = row_w // 2 + np_w // 2 + self._numpad_summary_gap
        self._summary_col.place(x=x, y=12, anchor=tk.NW)

    def _set_mode(self, mode: str):
        if not self.client:
            return
        self.input_mode = mode
        self._mode_buttons["amount"].config(
            bg=S.ACCENT if mode == "amount" else S.BG_CARD
        )
        self._mode_buttons["bonus"].config(
            bg=S.ACCENT if mode == "bonus" else S.BG_CARD
        )
        if mode == "amount":
            self.mode_hint.config(text="Введите сумму пополнения на клавиатуре ниже")
            self.numpad.set_value(str(self.selected) if self.selected else "", notify=False)
        else:
            max_b = self._max_bonus_allowed()
            self.mode_hint.config(
                text=(
                    f"Введите, сколько бонусов списать (доступно: {self.client.bonus_rub}, "
                    f"максимум к этой сумме: {max_b})"
                )
            )
            self.bonus_to_use = 0
            self.numpad.set_value("", notify=False)
            self._refresh_summary()

    def _bonus_numpad_text(self, bonus: int) -> str:
        return "" if bonus <= 0 else str(bonus)

    def _on_numpad_change(self, value: str):
        if self.input_mode == "bonus" and self.client:
            if value.isdigit() and value:
                self.bonus_to_use = int(value)
            else:
                self.bonus_to_use = 0
            self._clamp_bonus()
            display = self._bonus_numpad_text(self.bonus_to_use)
            if value.isdigit() and value:
                normalized = str(int(value))
                if normalized != value or display != (value if int(value) > 0 else ""):
                    self.numpad.set_value(display, notify=False)
            elif value and value != display:
                self.numpad.set_value(display, notify=False)
        else:
            if value.isdigit() and int(value) > 0:
                self.selected = int(value)
            else:
                self.selected = 0
            self._clamp_bonus()
        self._refresh_summary()

    def _pick(self, amount: int):
        self.input_mode = "amount"
        if self.client:
            self._set_mode("amount")
        self.selected = amount
        self.numpad.set_value(str(amount))
        self._refresh_summary()

    def _max_bonus_allowed(self) -> int:
        if not self.client:
            return 0
        amount = self.selected if self.selected > 0 else 0
        return min(self.client.bonus_rub, amount)

    def _clamp_bonus(self):
        max_b = self._max_bonus_allowed()
        if self.bonus_to_use > max_b:
            self.bonus_to_use = max_b

    def _refresh_summary(self):
        if not hasattr(self, "summary_label"):
            return
        amount = max(self.selected, 0)
        card = max(amount - self.bonus_to_use, 0)
        lines = [f"Время: {amount} сек", f"К оплате картой: {card} ₽"]
        if self.client:
            lines.append(f"Списать бонусов: {self.bonus_to_use}")
            if amount > 0 and card == 0 and self.bonus_to_use > 0:
                lines.append("Оплата полностью бонусами")
        self.summary_label.config(text="\n".join(lines))
        if hasattr(self, "pay_btn"):
            if self.client and amount > 0 and card == 0 and self.bonus_to_use > 0:
                self.pay_btn.config(text="Оплатить бонусами")
            else:
                self.pay_btn.config(text="Оплатить картой")

    def _validate_amount(self) -> Optional[int]:
        if self.selected < 10:
            show_warning(self, "Сумма", "Минимальное пополнение — 10 ₽")
            return None
        if self.selected > 9999:
            show_warning(self, "Сумма", "Слишком большая сумма")
            return None
        return self.selected

    def _validate_bonus(self, amount: int) -> bool:
        if not self.client or self.bonus_to_use <= 0:
            self.bonus_to_use = 0
            return True
        self._clamp_bonus()
        if self.bonus_to_use > self.client.bonus_rub:
            show_warning(
                self,
                "Бонусы",
                f"Доступно только {self.client.bonus_rub} бонусов",
            )
            return False
        if self.bonus_to_use > amount:
            show_warning(
                self,
                "Бонусы",
                "Нельзя списать бонусов больше суммы пополнения",
            )
            return False
        return True

    def _pay_card(self):
        if self.input_mode == "bonus":
            self._set_mode("amount")
        amount = self._validate_amount()
        if amount is None:
            return
        if not self._validate_bonus(amount):
            return

        if self.client:
            try:
                spend_bonuses(self.client.id, self.bonus_to_use)
            except ValueError:
                show_error(self, "Бонусы", "Не удалось списать бонусы")
                return

        self.app.start_session(amount, self.client)

    def _pay_from_balance(self):
        if not self.client:
            return
        amount = self._validate_amount()
        if amount is None:
            return
        if self.client.balance_rub < amount:
            show_warning(
                self,
                "Баланс",
                f"На счёте только {self.client.balance_rub} ₽",
            )
            return
        if not deduct_balance(self.client.id, amount):
            show_error(self, "Ошибка", "Не удалось списать баланс")
            return
        self.app.start_session(amount, self.client)
