"""
Main Application Window — NEF to JPG Converter.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
import os

from ui.file_list import FileListWidget, STATUS_OK, STATUS_ERROR, STATUS_RUNNING, STATUS_PENDING
from ui.settings_panel import SettingsPanel
from ui.progress_panel import ProgressPanel
from converters.nef_converter import convert_nef_to_jpg, get_output_path, is_valid_raw

# Try to import tkinterdnd2; fall back gracefully if not installed.
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False


class App(ctk.CTk):
    """Main application window."""

    APP_TITLE   = "NEF to JPG Converter"
    APP_VERSION = "1.0.0"
    MIN_W, MIN_H = 980, 660
    DEF_W, DEF_H = 1140, 740

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def __init__(self):
        super().__init__()

        # Enable drag-and-drop if available
        if _DND_AVAILABLE:
            try:
                self.TkdndVersion = TkinterDnD._require(self)
            except Exception:
                pass

        self._files: List[str] = []
        self._running = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self._cancel_flag = threading.Event()

        self._configure_window()
        self._build_ui()
        self._setup_drag_drop()

    def _configure_window(self):
        self.title(self.APP_TITLE)
        self.geometry(f"{self.DEF_W}x{self.DEF_H}")
        self.minsize(self.MIN_W, self.MIN_H)

        # Try to load icon
        icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.configure(fg_color="#141414")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=0)   # header
        self.grid_rowconfigure(1, weight=1)   # content
        self.grid_rowconfigure(2, weight=0)   # bottom bar
        self.grid_columnconfigure(0, weight=1, minsize=320)  # left
        self.grid_columnconfigure(1, weight=0, minsize=290)  # right

        self._build_header()
        self._build_left_panel()
        self._build_right_panel()
        self._build_bottom_bar()

    # ── Header ────────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="#0f0f0f", height=60, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        # Logo / title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=0, sticky="w")

        ctk.CTkLabel(
            title_frame,
            text="⬡",
            text_color="#e8a838",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkLabel(
            title_frame,
            text="NEF  ",
            text_color="#f0f0f0",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            title_frame,
            text="→ JPG",
            text_color="#e8a838",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=2)

        ctk.CTkLabel(
            title_frame,
            text=f" v{self.APP_VERSION}",
            text_color="#444444",
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=3)

        # Add files button in header
        self._add_btn = ctk.CTkButton(
            header,
            text="+ Agregar archivos",
            width=150,
            height=34,
            corner_radius=8,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            border_color="#e8a838",
            border_width=1,
            text_color="#e8a838",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._pick_files,
        )
        self._add_btn.grid(row=0, column=1, padx=10, pady=12, sticky="e")

        self._clear_btn = ctk.CTkButton(
            header,
            text="Limpiar lista",
            width=110,
            height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#2a2a2a",
            text_color="#666666",
            font=ctk.CTkFont(size=12),
            command=self._clear_files,
        )
        self._clear_btn.grid(row=0, column=2, padx=(0, 20), pady=12, sticky="e")

    # ── Left panel (file list + drop zone) ───────────────────────────

    def _build_left_panel(self):
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, padx=(12, 6), pady=10, sticky="nsew")
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Drop zone (visual hint at top)
        self._drop_zone = ctk.CTkFrame(
            left,
            fg_color="#1a1a1a",
            corner_radius=10,
            border_color="#2d2d2d",
            border_width=2,
        )
        self._drop_zone.grid(row=0, column=0, sticky="nsew")
        self._drop_zone.grid_rowconfigure(0, weight=1)
        self._drop_zone.grid_columnconfigure(0, weight=1)

        # File list widget fills the drop zone
        self._file_list = FileListWidget(
            self._drop_zone,
            on_files_changed=self._on_files_changed,
        )
        self._file_list.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Drag hint label overlay (shown when DnD available and list empty)
        if _DND_AVAILABLE:
            self._dnd_hint = ctk.CTkLabel(
                self._drop_zone,
                text="⬇  Arrastrá archivos .NEF aquí",
                text_color="#2d2d2d",
                font=ctk.CTkFont(size=13),
            )
            # Not shown initially

    # ── Right panel (settings) ────────────────────────────────────────

    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, padx=(6, 12), pady=10, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._settings = SettingsPanel(right)
        self._settings.grid(row=0, column=0, sticky="nsew")

    # ── Bottom bar (progress + convert button) ────────────────────────

    def _build_bottom_bar(self):
        bottom = ctk.CTkFrame(self, fg_color="#0f0f0f", corner_radius=0, height=200)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_propagate(False)

        # Progress panel
        self._progress = ProgressPanel(bottom)
        self._progress.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")

        # Convert / Cancel button
        btn_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="e")

        self._convert_btn = ctk.CTkButton(
            btn_frame,
            text="▶  Convertir a JPG",
            width=200,
            height=44,
            corner_radius=10,
            fg_color="#e8a838",
            hover_color="#ffbe4f",
            text_color="#1a1a1a",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_conversion,
        )
        self._convert_btn.grid(row=0, column=0, padx=(0, 8))

        self._cancel_btn = ctk.CTkButton(
            btn_frame,
            text="✕  Cancelar",
            width=110,
            height=44,
            corner_radius=10,
            fg_color="#2a2a2a",
            hover_color="#3a1515",
            text_color="#f87171",
            font=ctk.CTkFont(size=13),
            command=self._cancel_conversion,
            state="disabled",
        )
        self._cancel_btn.grid(row=0, column=1)

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------

    def _setup_drag_drop(self):
        if not _DND_AVAILABLE:
            return
        try:
            self._drop_zone.drop_target_register(DND_FILES)
            self._drop_zone.dnd_bind("<<Drop>>", self._on_drop)
            self._file_list.drop_target_register(DND_FILES)
            self._file_list.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event):
        raw = event.data
        # tkinterdnd2 returns paths wrapped in braces if they contain spaces
        paths = self.tk.splitlist(raw)
        valid = [p for p in paths if is_valid_raw(p)]
        invalid = len(paths) - len(valid)
        if valid:
            self._file_list.add_files(valid)
        if invalid > 0:
            messagebox.showwarning(
                "Archivos no válidos",
                f"{invalid} archivo(s) ignorados. Solo se aceptan archivos RAW (.NEF, .CR2, .ARW, .DNG…)",
                parent=self,
            )

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar archivos RAW",
            filetypes=[
                ("Archivos RAW", "*.nef *.NEF *.cr2 *.CR2 *.cr3 *.CR3 *.arw *.ARW *.dng *.DNG *.raf *.RAF *.rw2 *.RW2"),
                ("Nikon NEF", "*.nef *.NEF"),
                ("Todos los archivos", "*.*"),
            ],
        )
        valid = [p for p in paths if is_valid_raw(p)]
        if valid:
            self._file_list.add_files(list(valid))

    def _clear_files(self):
        if self._running:
            return
        self._file_list.clear()

    def _on_files_changed(self, files: List[str]):
        self._files = files
        enabled = "normal" if files and not self._running else "disabled"
        self._convert_btn.configure(state=enabled)

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def _start_conversion(self):
        if self._running or not self._files:
            return

        # Validate output dir
        output_dir = self._settings.output_dir
        if not output_dir:
            messagebox.showwarning(
                "Sin carpeta de destino",
                "Primero elegí una carpeta donde guardar los archivos convertidos.",
                parent=self,
            )
            return

        self._running = True
        self._cancel_flag.clear()
        files = list(self._files)

        # UI state
        self._convert_btn.configure(state="disabled", text="Convirtiendo…")
        self._cancel_btn.configure(state="normal")
        self._file_list.lock_all()
        self._settings.lock()
        self._file_list.reset_statuses()
        self._progress.reset(len(files))

        # Run in background thread
        thread = threading.Thread(
            target=self._run_conversion,
            args=(files, output_dir),
            daemon=True,
        )
        thread.start()

    def _run_conversion(self, files: List[str], output_dir: str):
        quality    = self._settings.quality
        max_dim    = self._settings.max_dimension
        overwrite  = self._settings.overwrite
        total      = len(files)
        done = ok = errors = 0

        max_workers = min(4, os.cpu_count() or 2)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for path in files:
                if self._cancel_flag.is_set():
                    break
                out = get_output_path(path, output_dir)
                future = executor.submit(
                    convert_nef_to_jpg,
                    path, out,
                    quality=quality,
                    max_dimension=max_dim,
                    overwrite=overwrite,
                )
                futures[future] = path
                self._schedule_ui(self._file_list.set_file_status, path, STATUS_RUNNING)

            for future in as_completed(futures):
                if self._cancel_flag.is_set():
                    break

                path = futures[future]
                try:
                    success, error_msg = future.result()
                except Exception as e:
                    success, error_msg = False, str(e)

                done += 1
                if success:
                    ok += 1
                    self._schedule_ui(self._file_list.set_file_status, path, STATUS_OK)
                else:
                    errors += 1
                    self._schedule_ui(self._file_list.set_file_status, path, STATUS_ERROR, error_msg)
                    self._schedule_ui(
                        self._progress.add_error, Path(path).name, error_msg
                    )

                self._schedule_ui(
                    self._progress.update_progress, done, ok, errors, total
                )

        self._schedule_ui(self._on_conversion_done, ok, errors, self._cancel_flag.is_set())

    def _on_conversion_done(self, ok: int, errors: int, cancelled: bool):
        self._running = False
        self._convert_btn.configure(
            state="normal" if self._files else "disabled",
            text="▶  Convertir a JPG",
        )
        self._cancel_btn.configure(state="disabled")
        self._file_list.unlock_all()
        self._settings.unlock()

        if cancelled:
            self._progress.set_status_text("Cancelado por el usuario")
        else:
            self._progress.set_complete(ok, errors)

    def _cancel_conversion(self):
        self._cancel_flag.set()
        self._cancel_btn.configure(state="disabled", text="Cancelando…")

    # ------------------------------------------------------------------
    # Thread-safe UI scheduling
    # ------------------------------------------------------------------

    def _schedule_ui(self, fn, *args, **kwargs):
        """Call fn with args on the main thread via after()."""
        self.after(0, fn, *args, **kwargs)
