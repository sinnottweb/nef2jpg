"""
Settings Panel — quality slider, resize options, overwrite toggle, output folder.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional


class SectionTitle(ctk.CTkLabel):
    def __init__(self, parent, text, **kwargs):
        super().__init__(
            parent,
            text=text,
            text_color="#e8a838",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
            **kwargs,
        )


class Divider(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=1, fg_color="#2d2d2d", **kwargs)


class SettingsPanel(ctk.CTkFrame):
    """
    Right-side panel with all conversion settings.
    """

    RESIZE_OPTIONS = {
        "Original":        None,
        "1920 px (FHD)":   1920,
        "3840 px (4K)":    3840,
        "Personalizado":   -1,
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#1e1e1e", corner_radius=10, **kwargs)

        self._output_dir: Optional[str] = None
        self._custom_size_var = tk.StringVar(value="2048")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        pad = {"padx": 16, "sticky": "ew"}

        # ── Output folder ──────────────────────────────────────────────
        SectionTitle(self, text="📂  Carpeta de destino").grid(
            row=0, column=0, pady=(16, 4), **pad
        )

        folder_frame = ctk.CTkFrame(self, fg_color="#252525", corner_radius=8)
        folder_frame.grid(row=1, column=0, pady=(0, 4), **pad)
        folder_frame.grid_columnconfigure(0, weight=1)

        self._folder_label = ctk.CTkLabel(
            folder_frame,
            text="Sin seleccionar",
            text_color="#666666",
            anchor="w",
            font=ctk.CTkFont(size=11),
        )
        self._folder_label.grid(row=0, column=0, padx=10, pady=8, sticky="ew")

        self._folder_btn = ctk.CTkButton(
            folder_frame,
            text="Elegir…",
            width=70,
            height=28,
            corner_radius=6,
            fg_color="#2d2d2d",
            hover_color="#e8a838",
            text_color="#cccccc",
            font=ctk.CTkFont(size=11),
            command=self._pick_folder,
        )
        self._folder_btn.grid(row=0, column=1, padx=(4, 8), pady=8)

        Divider(self).grid(row=2, column=0, pady=(8, 0), **pad)

        # ── JPEG Quality ───────────────────────────────────────────────
        quality_header = ctk.CTkFrame(self, fg_color="transparent")
        quality_header.grid(row=3, column=0, pady=(12, 0), **pad)
        quality_header.grid_columnconfigure(0, weight=1)

        SectionTitle(quality_header, text="🎨  Calidad JPEG").grid(
            row=0, column=0, sticky="w"
        )

        self._quality_value_label = ctk.CTkLabel(
            quality_header,
            text="90",
            text_color="#e8a838",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._quality_value_label.grid(row=0, column=1, sticky="e")

        self._quality_slider = ctk.CTkSlider(
            self,
            from_=50,
            to=100,
            number_of_steps=50,
            progress_color="#e8a838",
            button_color="#e8a838",
            button_hover_color="#ffbe4f",
            command=self._on_quality_change,
        )
        self._quality_slider.set(90)
        self._quality_slider.grid(row=4, column=0, pady=(6, 2), **pad)

        quality_hints = ctk.CTkFrame(self, fg_color="transparent")
        quality_hints.grid(row=5, column=0, padx=16, sticky="ew")
        quality_hints.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            quality_hints, text="Menor tamaño", text_color="#555555",
            font=ctk.CTkFont(size=10)
        ).grid(row=0, column=0)
        ctk.CTkLabel(
            quality_hints, text="Mayor calidad", text_color="#555555",
            font=ctk.CTkFont(size=10), anchor="e"
        ).grid(row=0, column=2)

        Divider(self).grid(row=6, column=0, pady=(12, 0), **pad)

        # ── Resize ──────────────────────────────────────────────────────
        SectionTitle(self, text="📐  Tamaño de salida").grid(
            row=7, column=0, pady=(12, 6), **pad
        )

        self._resize_var = tk.StringVar(value="Original")
        resize_frame = ctk.CTkFrame(self, fg_color="transparent")
        resize_frame.grid(row=8, column=0, **pad)
        resize_frame.grid_columnconfigure(0, weight=1)
        resize_frame.grid_columnconfigure(1, weight=1)

        options = list(self.RESIZE_OPTIONS.keys())
        for i, opt in enumerate(options):
            rb = ctk.CTkRadioButton(
                resize_frame,
                text=opt,
                variable=self._resize_var,
                value=opt,
                text_color="#cccccc",
                fg_color="#e8a838",
                hover_color="#ffbe4f",
                font=ctk.CTkFont(size=12),
                command=self._on_resize_change,
            )
            rb.grid(row=i // 2, column=i % 2, padx=4, pady=4, sticky="w")

        # Custom size input (hidden initially)
        self._custom_frame = ctk.CTkFrame(self, fg_color="#252525", corner_radius=8)
        # Not gridded initially

        ctk.CTkLabel(
            self._custom_frame,
            text="Lado mayor (px):",
            text_color="#aaaaaa",
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=0, padx=10, pady=8)

        self._custom_entry = ctk.CTkEntry(
            self._custom_frame,
            textvariable=self._custom_size_var,
            width=80,
            height=28,
            corner_radius=6,
            fg_color="#1a1a1a",
            border_color="#444444",
            text_color="#f0f0f0",
            font=ctk.CTkFont(size=12),
        )
        self._custom_entry.grid(row=0, column=1, padx=(0, 10), pady=8)

        ctk.CTkLabel(
            self._custom_frame,
            text="px",
            text_color="#666666",
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=2, padx=(0, 10), pady=8)

        Divider(self).grid(row=10, column=0, pady=(12, 0), **pad)

        # ── Overwrite ───────────────────────────────────────────────────
        SectionTitle(self, text="♻️  Archivos existentes").grid(
            row=11, column=0, pady=(12, 6), **pad
        )

        overwrite_frame = ctk.CTkFrame(self, fg_color="#252525", corner_radius=8)
        overwrite_frame.grid(row=12, column=0, pady=(0, 8), **pad)
        overwrite_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            overwrite_frame,
            text="Sobrescribir si ya existe",
            text_color="#cccccc",
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self._overwrite_switch = ctk.CTkSwitch(
            overwrite_frame,
            text="",
            progress_color="#e8a838",
            button_color="#ffffff",
            button_hover_color="#eeeeee",
            width=44,
        )
        self._overwrite_switch.select()
        self._overwrite_switch.grid(row=0, column=1, padx=12, pady=10)

        # Spacer
        ctk.CTkFrame(self, fg_color="transparent", height=8).grid(row=13, column=0)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_quality_change(self, value):
        self._quality_value_label.configure(text=str(int(value)))

    def _on_resize_change(self):
        if self._resize_var.get() == "Personalizado":
            self._custom_frame.grid(row=9, column=0, padx=16, pady=(4, 0), sticky="ew")
        else:
            self._custom_frame.grid_remove()

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Elegir carpeta de destino")
        if path:
            self._output_dir = path
            short = Path(path).name or path
            self._folder_label.configure(
                text=f"…/{short}",
                text_color="#f0f0f0",
            )

    # ------------------------------------------------------------------
    # Public getters
    # ------------------------------------------------------------------

    @property
    def quality(self) -> int:
        return int(self._quality_slider.get())

    @property
    def max_dimension(self) -> Optional[int]:
        key = self._resize_var.get()
        val = self.RESIZE_OPTIONS[key]
        if val == -1:
            try:
                return int(self._custom_size_var.get())
            except ValueError:
                return None
        return val

    @property
    def overwrite(self) -> bool:
        return self._overwrite_switch.get() == 1

    @property
    def output_dir(self) -> Optional[str]:
        return self._output_dir

    def lock(self):
        self._folder_btn.configure(state="disabled")
        self._quality_slider.configure(state="disabled")
        self._overwrite_switch.configure(state="disabled")

    def unlock(self):
        self._folder_btn.configure(state="normal")
        self._quality_slider.configure(state="normal")
        self._overwrite_switch.configure(state="normal")
