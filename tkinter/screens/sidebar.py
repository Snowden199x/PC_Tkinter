"""
sidebar.py — Left navigation sidebar shown after login.
"""

import tkinter as tk

from constants import (
    BG, WHITE, CREAM,
    TEXT_DARK, TEXT_MUTE, ACTIVE_NAV,
    load_icon
)


class Sidebar(tk.Frame):
    NAV = [
        ("🏠", "Home",    "home"),
        ("📋", "History", "history"),
        ("👛", "Wallets", "wallets"),
        ("👤", "Profile", "profile"),
    ]

    def __init__(self, parent, org, on_navigate, on_logout):
        super().__init__(parent, bg=BG, width=230)
        self.pack_propagate(False)
        self.org         = org
        self.on_navigate = on_navigate
        self._btns       = {}
        self._active     = None

        # Logo
        logo_frame = tk.Frame(self, bg=BG)
        logo_frame.pack(anchor="w", padx=14, pady=(14, 0))
        logo_img = load_icon("pocki_logo.png", (44, 44))
        if logo_img:
            lbl = tk.Label(logo_frame, image=logo_img, bg=BG)
            lbl.image = logo_img
            lbl.pack(side="left")
        tk.Label(logo_frame, text="PockiTrack", bg=BG, fg=TEXT_DARK,
                 font=("Poppins", 16, "bold")).pack(side="left", padx=6)

        # Org name
        tk.Label(self, text=org.get("org_name", ""), bg=BG, fg=TEXT_MUTE,
                 font=("Poppins", 8), wraplength=200).pack(anchor="w", padx=14, pady=(4, 0))

        # Nav items
        nav_frame = tk.Frame(self, bg=BG)
        nav_frame.pack(anchor="w", padx=0, pady=(20, 0), fill="x")
        for emoji, label, key in self.NAV:
            btn = tk.Button(
                nav_frame, text=f"  {emoji}  {label}",
                anchor="w", font=("Poppins", 11),
                bg=BG, fg=TEXT_MUTE, relief="flat",
                cursor="hand2", bd=0,
                activebackground=CREAM,
                command=lambda k=key: self._nav(k),
            )
            btn.pack(fill="x", padx=14, pady=3, ipady=8)
            self._btns[key] = btn

        # Logout
        tk.Frame(self, bg=CREAM, height=1).pack(fill="x", padx=20, pady=20)
        tk.Button(
            self, text="  ⎋  Logout",
            anchor="w", font=("Poppins", 11),
            bg=WHITE, fg=TEXT_MUTE, relief="flat",
            cursor="hand2", bd=0,
            activebackground=ACTIVE_NAV,
            activeforeground=WHITE,
            command=on_logout,
        ).pack(fill="x", padx=14, pady=4, ipady=8)

    def _nav(self, key):
        if self._active and self._active in self._btns:
            self._btns[self._active].config(bg=BG, fg=TEXT_MUTE)
        self._btns[key].config(bg=ACTIVE_NAV, fg=WHITE)
        self._active = key
        self.on_navigate(key)

    def set_active(self, key):
        self._nav(key)