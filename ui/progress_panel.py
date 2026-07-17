"""
Progress Panel — progress bar, counters, error log.
"""

import customtkinter as ctk
import tkinter as tk


class StatBox(ctk.CTkFrame):
    """Small stat counter box (label + number)."""

    def __init__(self, parent, label: str, color: str, **kwargs):
        super().__init__(parent, fg_color="#252525", corner_radius=8, **kwargs)

        self._count_var = tk.StringVar(value="0")

        ctk.CTkLabel(
            self,
            text=label,
            text_color="#777777",
            font=ctk.CTkFont(size=10),
        ).grid(row=0, column=0, padx=12, pady=(8, 2))

        ctk.CTkLabel(
            self,
            textvariable=self._count_var,
            text_color=color,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=1, column=0, padx=12, pady=(0, 8))

    def set(self, value: int):
        self._count_var.set(str(value))


class ProgressPanel(ctk.CTkFrame):
    """
    Bottom panel: stat boxes + progress bar + log.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#1a1a1a", corner_radius=10, **kwargs)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Stat boxes ─────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._pending_box  = StatBox(stats_frame, "PENDIENTES", "#888888")
        self._ok_box       = StatBox(stats_frame, "CONVERTIDOS", "#4ade80")
        self._error_box    = StatBox(stats_frame, "ERRORES",     "#f87171")

        self._pending_box.grid(row=0, column=0, padx=4, sticky="ew")
        self._ok_box.grid(     row=0, column=1, padx=4, sticky="ew")
        self._error_box.grid(  row=0, column=2, padx=4, sticky="ew")

        # ── Progress bar ────────────────────────────────────────────────
        bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        bar_frame.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="ew")
        bar_frame.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(
            bar_frame,
            height=8,
            progress_color="#e8a838",
            fg_color="#2d2d2d",
            corner_radius=4,
        )
        self._progress_bar.set(0)
        self._progress_bar.grid(row=0, column=0, sticky="ew", pady=4)

        self._progress_label = ctk.CTkLabel(
            bar_frame,
            text="Listo",
            text_color="#666666",
            font=ctk.CTkFont(size=11),
            anchor="e",
        )
        self._progress_label.grid(row=0, column=1, padx=(8, 0))

        # ── Error log (collapsible) ─────────────────────────────────────
        self._log_toggle_btn = ctk.CTkButton(
            self,
            text="▶  Ver errores",
            width=120,
            height=22,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#2a1515",
            text_color="#f87171",
            font=ctk.CTkFont(size=11),
            command=self._toggle_log,
        )
        # Hidden initially
        self._log_visible = False
        self._log_errors: list = []

        self._log_frame = ctk.CTkScrollableFrame(
            self,
            height=90,
            fg_color="#1a0a0a",
            corner_radius=6,
        )

        self._log_text = ctk.CTkLabel(
            self._log_frame,
            text="",
            text_color="#f87171",
            font=ctk.CTkFont(family="Consolas", size=11),
            justify="left",
            anchor="nw",
            wraplength=600,
        )
        self._log_text.grid(row=0, column=0, padx=8, pady=4, sticky="w")

        # Bottom padding
        ctk.CTkFrame(self, fg_color="transparent", height=8).grid(row=4, column=0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, total: int):
        self._pending_box.set(total)
        self._ok_box.set(0)
        self._error_box.set(0)
        self._progress_bar.set(0)
        self._progress_label.configure(text="0%")
        self._log_errors.clear()
        self._log_text.configure(text="")
        self._hide_log()

    def update_progress(self, done: int, ok: int, errors: int, total: int):
        pending = total - done
        self._pending_box.set(pending)
        self._ok_box.set(ok)
        self._error_box.set(errors)

        pct = (done / total) if total > 0 else 0
        self._progress_bar.set(pct)
        self._progress_label.configure(text=f"{int(pct * 100)}%")

    def set_status_text(self, text: str):
        self._progress_label.configure(text=text)

    def add_error(self, filename: str, message: str):
        self._log_errors.append(f"✗  {filename}: {message}")
        self._log_text.configure(text="\n".join(self._log_errors))
        self._log_toggle_btn.grid(row=2, column=0, padx=16, pady=(4, 0), sticky="w")

    def set_complete(self, ok: int, errors: int):
        if errors == 0:
            self._progress_label.configure(
                text=f"✓ Completado — {ok} archivos",
                text_color="#4ade80",
            )
        else:
            self._progress_label.configure(
                text=f"Finalizado con {errors} error{'es' if errors != 1 else ''}",
                text_color="#f87171",
            )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _toggle_log(self):
        if self._log_visible:
            self._hide_log()
        else:
            self._show_log()

    def _show_log(self):
        self._log_frame.grid(row=3, column=0, padx=16, pady=(4, 0), sticky="ew")
        self._log_toggle_btn.configure(text="▼  Ocultar errores")
        self._log_visible = True

    def _hide_log(self):
        self._log_frame.grid_remove()
        self._log_toggle_btn.configure(text="▶  Ver errores")
        self._log_visible = False
        self._log_toggle_btn.grid_remove()
