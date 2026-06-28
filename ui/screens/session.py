# -*- coding: utf-8 -*-
"""Экран мойки: таймер и выбор услуги."""

import tkinter as tk
from typing import Dict, Optional

from avtomoyka_v2.app_settings import pause_budget_seconds, session_warning_seconds
from avtomoyka_v2.services.client_service import Client
from avtomoyka_v2.services import session_service as ss
from avtomoyka_v2.ui import styles as S
from avtomoyka_v2.ui.widgets import touch_button


class SessionScreen(tk.Frame):
    def __init__(
        self,
        master,
        app,
        seconds: int,
        client: Optional[Client],
        free_mode: bool = False,
    ):
        super().__init__(master, bg=S.BG)
        self.app = app
        self.client = client
        self.free_mode = free_mode
        self.session = ss.start_session(
            seconds, client.id if client else None, free=free_mode
        )
        self._service_buttons: Dict[str, tk.Button] = {}
        self._tick_job = None
        self._blink_job = None
        self._blink_on = False
        self._running = True
        self._warning_sec = session_warning_seconds()
        self._timer_fg = S.MUTED

        # Таймер стартует только после выбора услуги
        self._timer_started = False
        self._is_paused = False
        self._pause_budget = pause_budget_seconds()

        self.title_label = tk.Label(
            self,
            text="Служебный режим — выберите услугу" if free_mode else "Выберите услугу для старта",
            font=S.FONT_HEAD,
            bg=S.BG,
            fg=S.WARNING if free_mode else S.FG,
        )
        self.title_label.pack(pady=(24, 0))

        tk.Label(
            self,
            text="1 ₽ = 1 сек  •  переключайте услуги в любой момент",
            font=S.FONT_BODY,
            bg=S.BG,
            fg=S.MUTED,
        ).pack(pady=4)

        self.remaining_caption = tk.Label(
            self,
            text="Осталось",
            font=S.FONT_SESSION_CAPTION,
            bg=S.BG,
            fg=S.MUTED,
        )
        self.remaining_caption.pack(pady=(8, 0))

        self.timer_label = tk.Label(
            self,
            text=self._fmt_time(seconds),
            font=S.FONT_SESSION_TIMER,
            bg=S.BG,
            fg=S.MUTED,
        )
        self.timer_label.pack(pady=(0, 8))

        self.pause_label = tk.Label(
            self,
            text=f"Пауза: доступно {self._pause_budget} сек",
            font=S.FONT_BODY,
            bg=S.BG,
            fg=S.MUTED,
        )
        self.pause_label.pack(pady=4)

        self.service_label = tk.Label(
            self, text="Услуга не выбрана", font=S.FONT_HEAD, bg=S.BG, fg=S.FG
        )
        self.service_label.pack(pady=8)

        grid = tk.Frame(self, bg=S.BG)
        grid.pack(pady=8, expand=True)

        services = ss.list_services()
        for i, svc in enumerate(services):
            r, c = divmod(i, 3)
            btn = touch_button(
                grid,
                svc.name,
                lambda code=svc.code, name=svc.name: self._select_service(code, name),
                width=12,
                bg=S.BG_CARD,
            )
            btn.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            self._service_buttons[svc.code] = btn

        controls = tk.Frame(self, bg=S.BG)
        controls.pack(pady=12)

        self.pause_btn = touch_button(
            controls,
            "Пауза",
            self._start_pause,
            bg=S.WARNING,
            state="disabled",
        )
        self.pause_btn.pack(side="left", padx=8)

        touch_button(controls, "Завершить досрочно", self._finish_early, bg=S.DANGER).pack(
            side="left", padx=8
        )

        self._schedule_tick()

    def _fmt_time(self, sec: int) -> str:
        sec = max(0, sec)
        return f"{sec // 60:02d}:{sec % 60:02d}"

    def _update_pause_label(self):
        if self._is_paused:
            self.pause_label.config(
                text=f"ПАУЗА  •  {self._pause_budget} сек",
                fg=S.WARNING,
            )
        else:
            self.pause_label.config(
                text=f"Пауза: доступно {self._pause_budget} сек",
                fg=S.MUTED if self._pause_budget > 0 else S.DANGER,
            )

    def _select_service(self, code: str, name: str):
        if not self._running:
            return

        if not self._timer_started:
            self._timer_started = True
            self.title_label.config(text="Идёт мойка")
            self.remaining_caption.config(fg=S.SUCCESS)
            self._timer_fg = S.SUCCESS
            self.timer_label.config(fg=S.SUCCESS)
            self._set_pause_button_state()

        if self._is_paused:
            self._resume_from_pause()

        ss.set_active_service(self.session.id, code)
        self.service_label.config(text=f"Активно: {name}")
        for c, btn in self._service_buttons.items():
            btn.config(bg=S.ACCENT if c == code else S.BG_CARD)

    def _resume_from_pause(self):
        self._is_paused = False
        self._set_pause_button_state()
        self._update_pause_label()

    def _set_pause_button_state(self):
        if not self._timer_started or self._pause_budget <= 0 or self._is_paused:
            self.pause_btn.config(state="disabled", text="Пауза")
        else:
            self.pause_btn.config(state="normal", text="Пауза")

    def _start_pause(self):
        if not self._timer_started or not self._running or self._is_paused:
            return
        if self._pause_budget <= 0:
            return
        self._is_paused = True
        ss.set_active_service(self.session.id, None)
        self.service_label.config(text="На паузе — выберите услугу для продолжения")
        for btn in self._service_buttons.values():
            btn.config(bg=S.BG_CARD)
        self._set_pause_button_state()
        self._update_pause_label()

    def _schedule_tick(self):
        if not self._running:
            return
        self._tick()
        self._tick_job = self.after(1000, self._schedule_tick)

    def _tick(self):
        if not self._running or not self._timer_started:
            return

        if self._is_paused:
            if self._pause_budget > 0:
                self._pause_budget -= 1
            self._update_pause_label()
            if self._pause_budget <= 0:
                self._resume_from_pause()
                self.service_label.config(text="Пауза закончилась — выберите услугу")
            return

        updated = ss.tick_session(self.session.id)
        if updated is None:
            self._end_session()
            return
        self.session = updated
        remaining = updated.seconds_remaining
        self._update_timer_display(remaining)
        if updated.status == "finished" or remaining <= 0:
            self._end_session()

    def _update_timer_display(self, remaining: int) -> None:
        self.timer_label.config(text=self._fmt_time(remaining))
        if not self._timer_started or self._is_paused:
            self._stop_blink()
            return
        if remaining <= self._warning_sec:
            self._start_blink()
        else:
            self._stop_blink()
            self.timer_label.config(fg=self._timer_fg)

    def _start_blink(self) -> None:
        if self._blink_job:
            return
        self.remaining_caption.config(fg=S.WARNING)
        self._blink_tick()

    def _blink_tick(self) -> None:
        if not self._running:
            return
        self._blink_on = not self._blink_on
        self.timer_label.config(fg=S.DANGER if self._blink_on else S.WARNING)
        self.remaining_caption.config(fg=S.DANGER if self._blink_on else S.WARNING)
        self._blink_job = self.after(500, self._blink_tick)

    def _stop_blink(self) -> None:
        if self._blink_job:
            self.after_cancel(self._blink_job)
            self._blink_job = None
        self._blink_on = False
        if self._timer_started and not self._is_paused:
            cap_fg = S.WARNING if self.session.seconds_remaining <= self._warning_sec else S.SUCCESS
            self.remaining_caption.config(fg=cap_fg if self._timer_started else S.MUTED)
            if self.session.seconds_remaining > self._warning_sec:
                self.timer_label.config(fg=self._timer_fg)

    def _finish_early(self):
        if not self._running:
            return
        fresh = ss.get_session(self.session.id)
        remaining = fresh.seconds_remaining if fresh else self.session.seconds_remaining
        bonus_refund = 0
        if self.client and remaining > 0:
            from avtomoyka_v2.services.client_service import add_bonus

            add_bonus(self.client.id, remaining)
            bonus_refund = remaining
        ss.finish_session(self.session.id)
        self._end_session(bonus_refund=bonus_refund)

    def _end_session(self, bonus_refund: int = 0):
        self._running = False
        self._stop_blink()
        if self._tick_job:
            self.after_cancel(self._tick_job)
        fresh = ss.get_session(self.session.id)
        if fresh:
            self.session = fresh
        used = self.session.seconds_total - max(0, self.session.seconds_remaining)
        self.app.show_finish(
            used,
            self.session.seconds_total,
            bonus_refund=bonus_refund,
        )
