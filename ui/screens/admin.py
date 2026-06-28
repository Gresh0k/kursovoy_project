# -*- coding: utf-8 -*-
"""Админ-панель v1.1: бесплатная мойка и управление клиентами."""

import tkinter as tk
from typing import Optional

from avtomoyka_v2.services.client_service import (
    Client,
    get_client,
    list_clients,
    set_blocked,
    set_bonus,
)
from avtomoyka_v2.ui import styles as S
from avtomoyka_v2.ui.dialogs import ask_yes_no, show_warning
from avtomoyka_v2.ui.widgets import Numpad, touch_button

FREE_PRESETS = [60, 120, 300, 600]


def _admin_btn(parent, text, command, bg=S.ACCENT, **kwargs):
    return touch_button(
        parent,
        text,
        command,
        bg=bg,
        font=S.FONT_ADMIN_BTN,
        padx=S.BTN_ADMIN_PADX,
        pady=S.BTN_ADMIN_PADY,
        **kwargs,
    )


class AdminScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=S.BG)
        self.app = app
        self._section = "free"
        self._selected_client_id: Optional[int] = None
        self._free_seconds = 120

        bottom = tk.Frame(self, bg=S.BG)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=4, padx=8)
        _admin_btn(bottom, "Выход", app.show_welcome, bg=S.BG_CARD).pack(fill=tk.X)

        header = tk.Frame(self, bg=S.BG)
        header.pack(fill=tk.X, pady=(8, 4), padx=10)
        tk.Label(
            header,
            text="Панель оператора",
            font=S.FONT_ADMIN_TITLE,
            bg=S.BG,
            fg=S.FG,
        ).pack(side=tk.LEFT)

        nav = tk.Frame(self, bg=S.BG)
        nav.pack(fill=tk.X, padx=10, pady=2)
        self._nav_buttons = {}
        for key, label in (("free", "Бесплатная мойка"), ("clients", "Клиенты")):
            btn = _admin_btn(
                nav,
                label,
                lambda k=key: self._switch_section(k),
                bg=S.ACCENT if key == "free" else S.BG_CARD,
            )
            btn.pack(side=tk.LEFT, padx=4, expand=True, fill=tk.X)
            self._nav_buttons[key] = btn

        self.body = tk.Frame(self, bg=S.BG)
        self.body.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        self._free_panel = tk.Frame(self.body, bg=S.BG)
        self._clients_panel = tk.Frame(self.body, bg=S.BG)

        self._build_free_panel()
        self._build_clients_panel()
        self._switch_section("free")

    def _switch_section(self, section: str):
        self._section = section
        for key, btn in self._nav_buttons.items():
            btn.config(bg=S.ACCENT if key == section else S.BG_CARD)
        self._free_panel.pack_forget()
        self._clients_panel.pack_forget()
        if section == "free":
            self._free_panel.pack(fill=tk.BOTH, expand=True)
        else:
            self._clients_panel.pack(fill=tk.BOTH, expand=True)
            self._refresh_clients()

    def _build_free_panel(self):
        tk.Label(
            self._free_panel,
            text="Запуск мойки без оплаты",
            font=S.FONT_ADMIN_BODY,
            bg=S.BG,
            fg=S.MUTED,
        ).pack(pady=(4, 8))

        presets = tk.Frame(self._free_panel, bg=S.BG)
        presets.pack(fill=tk.X, pady=4)
        for sec in FREE_PRESETS:
            _admin_btn(
                presets,
                f"{sec} сек",
                lambda s=sec: self._pick_free(s),
                bg=S.BG_CARD if sec != self._free_seconds else S.ACCENT,
            ).pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        self._free_label = tk.Label(
            self._free_panel,
            text=f"Выбрано: {self._free_seconds} сек",
            font=S.FONT_ADMIN_HEAD,
            bg=S.BG,
            fg=S.FG,
        )
        self._free_label.pack(pady=8)

        start_row = tk.Frame(self._free_panel, bg=S.BG)
        start_row.pack(fill=tk.X, padx=24, pady=4)
        _admin_btn(
            start_row,
            "Запустить бесплатную мойку",
            self._start_free,
            bg=S.SUCCESS,
        ).pack(fill=tk.X)

    def _pick_free(self, seconds: int):
        self._free_seconds = seconds
        self._free_label.config(text=f"Выбрано: {seconds} сек")
        for child in self._free_panel.winfo_children():
            if isinstance(child, tk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, tk.Button) and btn.cget("text").endswith(" сек"):
                        sec = int(btn.cget("text").split()[0])
                        btn.config(bg=S.ACCENT if sec == seconds else S.BG_CARD)

    def _start_free(self):
        ask_yes_no(
            self,
            "Бесплатная мойка",
            f"Запустить сессию на {self._free_seconds} сек без оплаты?",
            on_yes=lambda: self.app.start_session(
                self._free_seconds, None, free_mode=True
            ),
        )

    def _build_clients_panel(self):
        toolbar = tk.Frame(self._clients_panel, bg=S.BG)
        toolbar.pack(fill=tk.X, pady=(0, 4))
        _admin_btn(toolbar, "Обновить", self._refresh_clients, bg=S.BG_CARD).pack(
            side=tk.LEFT, padx=(0, 4), expand=True, fill=tk.X
        )
        _admin_btn(toolbar, "Заблокировать", self._block_client, bg=S.DANGER).pack(
            side=tk.LEFT, padx=2, expand=True, fill=tk.X
        )
        _admin_btn(toolbar, "Разблокировать", self._unblock_client, bg=S.SUCCESS).pack(
            side=tk.LEFT, padx=2, expand=True, fill=tk.X
        )

        list_frame = tk.Frame(self._clients_panel, bg=S.BG)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._client_list = tk.Listbox(
            list_frame,
            font=("Segoe UI", 12),
            bg=S.BG_CARD,
            fg=S.FG,
            selectbackground=S.ACCENT,
            yscrollcommand=scroll.set,
        )
        self._client_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self._client_list.yview)
        self._client_list.bind("<<ListboxSelect>>", self._on_client_select)

        self._client_info = tk.Label(
            self._clients_panel,
            text="Выберите клиента в списке",
            font=S.FONT_ADMIN_BODY,
            bg=S.BG,
            fg=S.MUTED,
            justify=tk.LEFT,
        )
        self._client_info.pack(anchor=tk.W, pady=(0, 4))

        bonus_section = tk.Frame(self._clients_panel, bg=S.BG_CARD, padx=10, pady=8)
        bonus_section.pack(fill=tk.X)

        tk.Label(
            bonus_section,
            text="Бонусы: «Сброс» → введите число → «Применить»",
            font=S.FONT_ADMIN_BODY,
            bg=S.BG_CARD,
            fg=S.MUTED,
        ).pack(anchor=tk.W, pady=(0, 4))

        bonus_row = tk.Frame(bonus_section, bg=S.BG_CARD)
        bonus_row.pack(fill=tk.X)

        self._bonus_numpad = Numpad(
            bonus_row, lambda _v: None, max_len=5, compact=True
        )
        self._bonus_numpad.pack(side=tk.LEFT, padx=(0, 12))

        bonus_side = tk.Frame(bonus_row, bg=S.BG_CARD)
        bonus_side.pack(side=tk.LEFT, anchor=tk.N)

        self._bonus_hint = tk.Label(
            bonus_side,
            text="Выберите клиента",
            font=S.FONT_ADMIN_BODY,
            bg=S.BG_CARD,
            fg=S.MUTED,
            justify=tk.LEFT,
            wraplength=220,
        )
        self._bonus_hint.pack(pady=(0, 6))

        btn_col = tk.Frame(bonus_side, bg=S.BG_CARD)
        btn_col.pack(fill=tk.X)
        _admin_btn(btn_col, "Применить", self._bonus_apply, bg=S.ACCENT).pack(
            side=tk.LEFT, padx=2, expand=True, fill=tk.X
        )
        _admin_btn(btn_col, "Обнулить", self._bonus_zero, bg=S.BG).pack(
            side=tk.LEFT, padx=2, expand=True, fill=tk.X
        )

        self._clients_cache: list[Client] = []

    def _refresh_clients(self):
        self._clients_cache = list_clients()
        self._client_list.delete(0, tk.END)
        for c in self._clients_cache:
            status = "БЛОК" if c.is_blocked else "OK"
            self._client_list.insert(
                tk.END,
                f"{c.phone}  |  {c.balance_rub} ₽  |  бонус {c.bonus_rub}  |  {status}",
            )
        self._selected_client_id = None
        self._client_info.config(text="Выберите клиента в списке", fg=S.MUTED)
        self._bonus_hint.config(text="Выберите клиента", fg=S.MUTED)
        self._bonus_numpad.set_value("", notify=False)

    def _on_client_select(self, _event=None):
        sel = self._client_list.curselection()
        if not sel:
            return
        client = self._clients_cache[sel[0]]
        self._selected_client_id = client.id
        self._client_info.config(
            text=(
                f"{client.phone}  •  баланс {client.balance_rub} ₽  •  "
                f"бонусы {client.bonus_rub}  •  "
                f"{'заблокирован' if client.is_blocked else 'активен'}"
            ),
            fg=S.FG,
        )
        self._bonus_hint.config(
            text=f"Сейчас: {client.bonus_rub}. Сброс → новое число",
            fg=S.SUCCESS,
        )
        self._bonus_numpad.set_value("", notify=False)

    def _get_selected(self) -> Optional[Client]:
        if self._selected_client_id is None:
            show_warning(self, "Клиент", "Выберите клиента в списке")
            return None
        return get_client(self._selected_client_id)

    def _block_client(self):
        client = self._get_selected()
        if not client:
            return
        set_blocked(client.id, True)
        self._refresh_clients()

    def _unblock_client(self):
        client = self._get_selected()
        if not client:
            return
        set_blocked(client.id, False)
        self._refresh_clients()

    def _parse_bonus_value(self) -> Optional[int]:
        raw = self._bonus_numpad.value.strip()
        if not raw.isdigit():
            show_warning(self, "Бонусы", "Введите количество бонусов (целое число)")
            return None
        return int(raw)

    def _bonus_apply(self):
        client = self._get_selected()
        if not client:
            return
        amount = self._parse_bonus_value()
        if amount is None:
            return
        ask_yes_no(
            self,
            "Бонусы",
            f"Установить {amount} бонусов для клиента {client.phone}?",
            on_yes=lambda cid=client.id, a=amount: self._set_bonus(cid, a),
        )

    def _set_bonus(self, client_id: int, amount: int):
        set_bonus(client_id, amount)
        self._refresh_clients()
        idx = next(
            (i for i, c in enumerate(self._clients_cache) if c.id == client_id),
            None,
        )
        if idx is not None:
            self._client_list.selection_clear(0, tk.END)
            self._client_list.selection_set(idx)
            self._client_list.event_generate("<<ListboxSelect>>")

    def _bonus_zero(self):
        client = self._get_selected()
        if not client:
            return
        self._bonus_numpad.set_value("0", notify=False)
        ask_yes_no(
            self,
            "Бонусы",
            f"Обнулить бонусы клиента {client.phone}?",
            on_yes=lambda cid=client.id: self._set_bonus(cid, 0),
        )
