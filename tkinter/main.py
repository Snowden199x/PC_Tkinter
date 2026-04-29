"""
main.py – PockiTrack entry point
Handles app window, screen transitions, and sidebar routing.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "screens"))

import tkinter as tk
from tkinter import font as tkfont

from constants import *
from screens.sidebar       import Sidebar
from screens.start_screen  import StartScreen
from screens.login_screen  import LoginScreen
from screens.home_screen   import HomeScreen
from screens.history_screen import HistoryScreen
from screens.wallet_screen import WalletScreen
from screens.profile_screen import ProfileScreen


class PockiTrackApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.resizable(True, True)
        self.configure(bg=BG_CREAM)

        # ── Load Poppins if available ─────────────────────────────────
        self._try_load_poppins()

        # ── App state ─────────────────────────────────────────────────
        self._logged_in = False
        self._current   = None

        # Outer container
        self._shell = tk.Frame(self, bg=BG_CREAM)
        self._shell.pack(fill="both", expand=True)

        # Sidebar (hidden until logged in)
        self._sidebar = None
        self._content = tk.Frame(self._shell, bg=BG_CREAM)
        self._content.pack(side="right", fill="both", expand=True)

        # Start on the start screen
        self._show("start")

    # ── Poppins font loader ───────────────────────────────────────────
    def _try_load_poppins(self):
        """Try to register Poppins from a fonts/ directory if present."""
        fonts_dir = os.path.join(BASE_DIR, "fonts")
        if not os.path.isdir(fonts_dir):
            return
        try:
            from tkinter import font as tkfont
            for f in os.listdir(fonts_dir):
                if f.lower().endswith((".ttf", ".otf")):
                    path = os.path.join(fonts_dir, f)
                    self.tk.call("font", "create", f.split(".")[0])
                    try:
                        self.tk.call("lappend", "::auto_path", fonts_dir)
                    except Exception:
                        pass
        except Exception:
            pass

    # ── Navigation ────────────────────────────────────────────────────
    def _show(self, screen_name):
        """Destroy current screen and show the requested one."""
        # clear content area
        for w in self._content.winfo_children():
            w.destroy()

        if screen_name == "start":
            self._hide_sidebar()
            StartScreen(self._content,
                        on_login=lambda: self._show("login")).pack(
                fill="both", expand=True)

        elif screen_name == "login":
            self._hide_sidebar()
            LoginScreen(self._content,
                        on_login_success=self._post_login,
                        on_back=lambda: self._show("start")).pack(
                fill="both", expand=True)

        elif screen_name == "home":
            self._show_sidebar()
            HomeScreen(self._content).pack(fill="both", expand=True)

        elif screen_name == "history":
            self._show_sidebar()
            HistoryScreen(self._content).pack(fill="both", expand=True)

        elif screen_name == "wallet":
            self._show_sidebar()
            WalletScreen(self._content).pack(fill="both", expand=True)

        elif screen_name == "profile":
            self._show_sidebar()
            ProfileScreen(self._content).pack(fill="both", expand=True)

        elif screen_name == "logout":
            self._hide_sidebar()
            self._logged_in = False
            self._show("start")

        self._current = screen_name
        if self._sidebar and screen_name in (
                "home", "history", "wallet", "profile"):
            self._sidebar.set_active(screen_name)

    def _post_login(self):
        self._logged_in = True
        self._show("home")

    def _show_sidebar(self):
        if self._sidebar is None:
            self._sidebar = Sidebar(self._shell,
                                    on_navigate=self._show)
            self._sidebar.pack(side="left", fill="y")

    def _hide_sidebar(self):
        if self._sidebar:
            self._sidebar.pack_forget()
            self._sidebar.destroy()
            self._sidebar = None


if __name__ == "__main__":
    app = PockiTrackApp()
    app.mainloop()
