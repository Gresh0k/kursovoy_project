# -*- coding: utf-8 -*-
"""Общие виджеты для сенсорного интерфейса."""

import tkinter as tk
from tkinter import ttk

from avtomoyka_v2.ui import styles as S

NUMPAD_FONT = ("Segoe UI", 16, "bold")
NUMPAD_PADX = 10
NUMPAD_PADY = 8


def touch_button(parent, text, command, bg=S.ACCENT, fg=S.FG, font=S.FONT_BTN, **kwargs):
    padx = kwargs.pop("padx", S.BTN_PADX)
    pady = kwargs.pop("pady", S.BTN_PADY)
    btn = tk.Button(
        parent,
        text=text,
        font=font,
        bg=bg,
        fg=fg,
        activebackground=S.ACCENT_ACTIVE,
        activeforeground=S.FG,
        relief="flat",
        cursor="hand2",
        command=command,
        padx=padx,
        pady=pady,
        **kwargs,
    )
    return btn


def numpad_button(parent, text, command, width=5, font=None, padx=None, pady=None):
    return tk.Button(
        parent,
        text=text,
        font=font or NUMPAD_FONT,
        bg=S.BG_CARD,
        fg=S.FG,
        activebackground=S.ACCENT,
        activeforeground=S.FG,
        relief="flat",
        cursor="hand2",
        command=command,
        width=width,
        padx=padx if padx is not None else NUMPAD_PADX,
        pady=pady if pady is not None else NUMPAD_PADY,
    )


class Numpad(ttk.Frame):
    """Экранная цифровая клавиатура для телефона и суммы."""

    def __init__(self, master, on_change, max_len=11, compact=False):
        super().__init__(master)
        self.on_change = on_change
        self.max_len = max_len
        self._value = ""

        if compact:
            disp_font = ("Segoe UI", 14, "bold")
            btn_font = ("Segoe UI", 11, "bold")
            btn_width = 4
            btn_padx, btn_pady = 4, 3
            grid_pad = 2
            disp_width = 10
            disp_pady = 2
        else:
            disp_font = S.FONT_HEAD
            btn_font = NUMPAD_FONT
            btn_width = 6
            btn_padx, btn_pady = NUMPAD_PADX, NUMPAD_PADY
            grid_pad = 4
            disp_width = 16
            disp_pady = 8

        display = tk.Label(
            self,
            text="—",
            font=disp_font,
            bg=S.BG_CARD,
            fg=S.FG,
            width=disp_width,
            pady=disp_pady,
        )
        display.pack(pady=2 if compact else 4)
        self.display = display

        grid = tk.Frame(self, bg=S.BG)
        grid.pack()
        keys = [
            ("1", "1"), ("2", "2"), ("3", "3"),
            ("4", "4"), ("5", "5"), ("6", "6"),
            ("7", "7"), ("8", "8"), ("9", "9"),
            ("Сброс", "C"), ("0", "0"), ("←", "BACK"),
        ]
        for i, (label, code) in enumerate(keys):
            r, c = divmod(i, 3)
            numpad_button(
                grid,
                label,
                lambda k=code: self._press(k),
                width=btn_width,
                font=btn_font,
                padx=btn_padx,
                pady=btn_pady,
            ).grid(row=r, column=c, padx=grid_pad, pady=grid_pad)

    @property
    def value(self) -> str:
        return self._value

    def set_value(self, value: str, notify: bool = True):
        self._value = value[: self.max_len]
        self.display.config(text=self._value or "—")
        if notify:
            self.on_change(self._value)

    def _press(self, key: str):
        if key == "C":
            self._value = ""
        elif key == "BACK":
            self._value = self._value[:-1]
        elif len(self._value) < self.max_len:
            self._value += key
        self.display.config(text=self._value or "—")
        self.on_change(self._value)


class PinPad(ttk.Frame):
    """Клавиатура для 4-значного кода (отображение скрыто)."""

    def __init__(self, master, on_change, pin_length=4):
        super().__init__(master)
        self.on_change = on_change
        self.pin_length = pin_length
        self._value = ""

        self.display = tk.Label(
            self,
            text="—",
            font=("Segoe UI", 28, "bold"),
            bg=S.BG_CARD,
            fg=S.FG,
            width=10,
            pady=12,
        )
        self.display.pack(pady=4)

        grid = tk.Frame(self, bg=S.BG)
        grid.pack()
        keys = [
            ("1", "1"), ("2", "2"), ("3", "3"),
            ("4", "4"), ("5", "5"), ("6", "6"),
            ("7", "7"), ("8", "8"), ("9", "9"),
            ("Сброс", "C"), ("0", "0"), ("←", "BACK"),
        ]
        for i, (label, code) in enumerate(keys):
            r, c = divmod(i, 3)
            numpad_button(grid, label, lambda k=code: self._press(k), width=6).grid(
                row=r, column=c, padx=4, pady=4
            )

    @property
    def value(self) -> str:
        return self._value

    def _masked(self) -> str:
        return "●" * len(self._value) if self._value else "—"

    def set_value(self, value: str, notify: bool = True):
        self._value = value[: self.pin_length]
        self.display.config(text=self._masked())
        if notify:
            self.on_change(self._value)

    def clear(self):
        self.set_value("", notify=False)

    def _press(self, key: str):
        if key == "C":
            self._value = ""
        elif key == "BACK":
            self._value = self._value[:-1]
        elif len(self._value) < self.pin_length:
            self._value += key
        self.display.config(text=self._masked())
        self.on_change(self._value)


class BonusPicker(tk.Frame):
    """Выбор количества бонусов без второй полной клавиатуры."""

    def __init__(self, master, on_change):
        super().__init__(master, bg=S.BG)
        self.on_change = on_change
        self._value = 0

        self.display = tk.Label(
            self,
            text="0",
            font=S.FONT_HEAD,
            bg=S.BG_CARD,
            fg=S.FG,
            width=12,
            pady=8,
        )
        self.display.pack(pady=4)

        row1 = tk.Frame(self, bg=S.BG)
        row1.pack(pady=2)
        for label, delta in [("-10", -10), ("-1", -1), ("+1", 1), ("+10", +10)]:
            touch_button(
                row1,
                label,
                lambda d=delta: self._add(d),
                bg=S.BG_CARD,
                width=5,
            ).pack(side=tk.LEFT, padx=4)

        row2 = tk.Frame(self, bg=S.BG)
        row2.pack(pady=4)
        touch_button(row2, "0", lambda: self._set(0), bg=S.BG_CARD, width=6).pack(
            side=tk.LEFT, padx=4
        )
        touch_button(row2, "Макс.", self._max_callback, bg=S.ACCENT, width=8).pack(
            side=tk.LEFT, padx=4
        )

        self._max_fn = None

    def set_max_callback(self, fn):
        self._max_fn = fn

    def set_value(self, value: int, notify: bool = True):
        self._value = max(0, value)
        self.display.config(text=str(self._value))
        if notify:
            self.on_change(self._value)

    @property
    def value(self) -> int:
        return self._value

    def _set(self, value: int):
        self.set_value(value)

    def _add(self, delta: int):
        self.set_value(self._value + delta)

    def _max_callback(self):
        if self._max_fn:
            self.set_value(self._max_fn())
