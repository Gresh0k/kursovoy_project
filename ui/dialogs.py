# -*- coding: utf-8 -*-
"""Встроенные диалоги в стиле постамата (без системных окон)."""

import tkinter as tk
from typing import Callable, Optional

from avtomoyka_v2.ui import styles as S
from avtomoyka_v2.ui.widgets import touch_button


def _close_overlay(overlay: tk.Frame) -> None:
    overlay.destroy()


def _clear_overlays(parent: tk.Widget) -> None:
    for child in parent.winfo_children():
        if getattr(child, "_kiosk_overlay", False):
            child.destroy()


def _show_overlay(
    parent: tk.Widget,
    title: str,
    message: str,
    title_color: str,
    buttons: list[tuple[str, Callable[[], None], str]],
) -> None:
    _clear_overlays(parent)

    overlay = tk.Frame(parent, bg=S.BG)
    overlay._kiosk_overlay = True  # type: ignore[attr-defined]
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    overlay.lift()

    dim = tk.Frame(overlay, bg="#0d1117")
    dim.place(relx=0, rely=0, relwidth=1, relheight=1)

    card = tk.Frame(dim, bg=S.BG_CARD, padx=36, pady=28)
    card.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    tk.Label(card, text=title, font=S.FONT_HEAD, bg=S.BG_CARD, fg=title_color).pack(
        pady=(0, 12)
    )
    tk.Label(
        card,
        text=message,
        font=S.FONT_BODY,
        bg=S.BG_CARD,
        fg=S.FG,
        justify=tk.CENTER,
        wraplength=420,
    ).pack(pady=(0, 20))

    btn_row = tk.Frame(card, bg=S.BG_CARD)
    btn_row.pack(fill=tk.X)

    for label, action, bg in buttons:

        def make_cmd(act: Callable[[], None]) -> Callable[[], None]:
            def cmd() -> None:
                _close_overlay(overlay)
                act()

            return cmd

        touch_button(
            btn_row,
            label,
            make_cmd(action),
            bg=bg,
            font=("Segoe UI", 18, "bold"),
            padx=20,
            pady=14,
        ).pack(
            side=tk.LEFT,
            padx=6,
            expand=True,
            fill=tk.X,
        )


def show_warning(
    parent: tk.Widget,
    title: str,
    message: str,
    on_close: Optional[Callable[[], None]] = None,
) -> None:
    _show_overlay(
        parent,
        title,
        message,
        S.WARNING,
        [("OK", on_close or (lambda: None), S.ACCENT)],
    )


def show_error(
    parent: tk.Widget,
    title: str,
    message: str,
    on_close: Optional[Callable[[], None]] = None,
) -> None:
    _show_overlay(
        parent,
        title,
        message,
        S.DANGER,
        [("OK", on_close or (lambda: None), S.ACCENT)],
    )


def ask_yes_no(
    parent: tk.Widget,
    title: str,
    message: str,
    on_yes: Callable[[], None],
    on_no: Optional[Callable[[], None]] = None,
) -> None:
    _show_overlay(
        parent,
        title,
        message,
        S.ACCENT,
        [
            ("Да", on_yes, S.SUCCESS),
            ("Нет", on_no or (lambda: None), S.BG_CARD),
        ],
    )
