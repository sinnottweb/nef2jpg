"""
NEF to JPG Converter — Entry point.
"""

import sys
import customtkinter as ctk


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    from ui.app import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
