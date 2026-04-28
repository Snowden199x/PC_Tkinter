"""
start_screen.py — Splash/Start screen shown before login.
"""

import tkinter as tk
from constants import (
    BG, TEXT_DARK, TEXT_MUTE, ACTIVE_NAV,
    styled_btn, load_icon
)


class StartScreen(tk.Frame):
    def __init__(self, master, on_login_click):
        """
        master         : root Tk window
        on_login_click : callback to open the login window
        """
        super().__init__(master, bg=BG)
        self._on_login_click = on_login_click
        self._build()

    def _build(self):
        center = tk.Frame(self, bg=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        logo_img = load_icon("pocki_logo.png", (80, 80))
        if logo_img:
            lbl = tk.Label(center, image=logo_img, bg=BG)
            lbl.image = logo_img
            lbl.pack(pady=(0, 8))

        tk.Label(
            center, text="PockiTrack",
            bg=BG, fg=TEXT_DARK,
            font=("Poppins", 32, "bold"),
        ).pack()

        tk.Label(
            center, text="Organization Financial Management",
            bg=BG, fg=TEXT_MUTE,
            font=("Poppins", 12),
        ).pack(pady=(4, 40))

        styled_btn(
            center,
            "  Log in to your Organization  ",
            self._on_login_click,
            bg=ACTIVE_NAV,
            font=("Poppins", 13, "bold"),
        ).pack(ipady=10, ipadx=20)

        tk.Label(
            center,
            text="Developed by Snowden, Yngrie & Zoo · LSPU-SCC",
            bg=BG, fg="#AAAAAA",
            font=("Poppins", 8),
        ).pack(pady=(40, 0))