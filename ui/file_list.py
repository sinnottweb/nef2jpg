"""
File List Widget — shows loaded NEF files with per-file status icons.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Callable, Dict, List


# Status codes
STATUS_PENDING  = "pending"
STATUS_OK       = "ok"
STATUS_ERROR    = "error"
STATUS_RUNNING  = "running"

STATUS_COLORS = {
    STATUS_PENDING: "#888888",
    STATUS_OK:      "#4ade80",
    STATUS_ERROR:   "#f87171",
    STATUS_RUNNING: "#e8a838",
}

STATUS_ICONS = {
    STATUS_PENDING: "○",
    STATUS_OK:      "✓",
    STATUS_ERROR:   "✗",
    STATUS_RUNNING: "⟳",
}


class FileRow(ctk.CTkFrame):
    """Single file row in the list."""

    def __init__(self, parent, path: str, on_remove: Callable[[str], None], **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.path = path
        self._on_remove = on_remove
        self.columnconfigure(1, weight=1)

        # Status icon
        self._status_label = ctk.CTkLabel(
            self,
            text=STATUS_ICONS[STATUS_PENDING],
            text_color=STATUS_COLORS[STATUS_PENDING],
            width=22,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._status_label.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")

        # File name
        name = Path(path).name
        self._name_label = ctk.CTkLabel(
            self,
            text=name,
            text_color="#d0d0d0",
            anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self._name_label.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        # Remove button
        self._remove_btn = ctk.CTkButton(
            self,
            text="✕",
            width=24,
            height=24,
            corner_radius=4,
            fg_color="transparent",
            hover_color="#3a2020",
            text_color="#666666",
            font=ctk.CTkFont(size=11),
            command=self._remove,
        )
        self._remove_btn.grid(row=0, column=2, padx=(4, 6), pady=4)

    def _remove(self):
        self._on_remove(self.path)

    def set_status(self, status: str, message: str = ""):
        color = STATUS_COLORS.get(status, "#888888")
        icon  = STATUS_ICONS.get(status, "?")
        self._status_label.configure(text=icon, text_color=color)
        if status == STATUS_ERROR and message:
            self._name_label.configure(
                text=f"{Path(self.path).name}  — {message}",
                text_color="#f87171",
            )
        elif status == STATUS_OK:
            self._name_label.configure(
                text=Path(self.path).name,
                text_color="#d0d0d0",
            )

    def lock(self):
        """Disable remove button during conversion."""
        self._remove_btn.configure(state="disabled")

    def unlock(self):
        self._remove_btn.configure(state="normal")


class FileListWidget(ctk.CTkFrame):
    """
    Scrollable list of loaded NEF files with status indicators.
    Exposes add_files(), clear(), set_file_status(), lock/unlock.
    """

    def __init__(self, parent, on_files_changed: Callable[[List[str]], None], **kwargs):
        super().__init__(parent, fg_color="#1e1e1e", corner_radius=10, **kwargs)
        self._on_files_changed = on_files_changed
        self._rows: Dict[str, FileRow] = {}   # path -> FileRow

        self._build()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="#2a2a2a", corner_radius=8, height=38)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="📁  Archivos cargados",
            text_color="#e8a838",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=12, pady=0, sticky="w")

        self._count_label = ctk.CTkLabel(
            header,
            text="0 archivos",
            text_color="#666666",
            font=ctk.CTkFont(size=11),
        )
        self._count_label.grid(row=0, column=1, padx=12, pady=0, sticky="e")

        # Scrollable area
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#333333",
            scrollbar_button_hover_color="#e8a838",
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self._scroll.columnconfigure(0, weight=1)

        # Empty state label
        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="Arrastrá archivos .NEF aquí\no usá el botón +",
            text_color="#444444",
            font=ctk.CTkFont(size=13),
            justify="center",
        )
        self._empty_label.grid(row=0, column=0, pady=60)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def add_files(self, paths: List[str]):
        """Add new files (deduplicates automatically)."""
        added = False
        for path in paths:
            if path not in self._rows:
                row = FileRow(self._scroll, path, on_remove=self._remove_file)
                row.grid(
                    row=len(self._rows),
                    column=0,
                    sticky="ew",
                    padx=2,
                    pady=2,
                )
                self._rows[path] = row
                added = True

        if added:
            self._refresh_empty_state()
            self._update_count()
            self._on_files_changed(list(self._rows.keys()))

    def _remove_file(self, path: str):
        if path in self._rows:
            self._rows[path].destroy()
            del self._rows[path]
            # Re-grid remaining rows
            for i, row in enumerate(self._rows.values()):
                row.grid(row=i, column=0, sticky="ew", padx=2, pady=2)
            self._refresh_empty_state()
            self._update_count()
            self._on_files_changed(list(self._rows.keys()))

    def clear(self):
        for row in self._rows.values():
            row.destroy()
        self._rows.clear()
        self._refresh_empty_state()
        self._update_count()
        self._on_files_changed([])

    def set_file_status(self, path: str, status: str, message: str = ""):
        if path in self._rows:
            self._rows[path].set_status(status, message)

    def lock_all(self):
        for row in self._rows.values():
            row.lock()

    def unlock_all(self):
        for row in self._rows.values():
            row.unlock()

    def get_files(self) -> List[str]:
        return list(self._rows.keys())

    def reset_statuses(self):
        for row in self._rows.values():
            row.set_status(STATUS_PENDING)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _refresh_empty_state(self):
        if self._rows:
            self._empty_label.grid_remove()
        else:
            self._empty_label.grid(row=0, column=0, pady=60)

    def _update_count(self):
        n = len(self._rows)
        self._count_label.configure(
            text=f"{n} {'archivo' if n == 1 else 'archivos'}"
        )
