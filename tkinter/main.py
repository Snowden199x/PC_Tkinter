"""
main.py — Entry point for PockiTrack Desktop (PRES side).
Run with: python main.py
"""

import tkinter as tk
from tkinter import messagebox

from constants import BG, supabase, load_icon
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

import os

from screens.start_screen   import StartScreen
from screens.login_screen   import LoginWindow
from screens.home_screen    import HomeTab
from screens.history_screen import HistoryTab
from screens.wallet_screen  import WalletsTab
from screens.profile_screen import ProfileTab
from screens.sidebar        import Sidebar


class PockiTrackApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PockiTrack")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._set_icon()
        self._org = None
        self._show_start()

    def _set_icon(self):
        try:
            if PIL_OK and os.path.exists("pocki_logo.png"):
                img   = Image.open("pocki_logo.png").resize((64, 64), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.iconphoto(True, photo)
                self._icon_ref = photo
        except Exception:
            pass

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ── Start / Splash ─────────────────────────────────────
    def _show_start(self):
        self._clear()
        screen = StartScreen(self, on_login_click=self._open_login)
        screen.pack(fill="both", expand=True)

    # ── Login ───────────────────────────────────────────────
    def _open_login(self):
        LoginWindow(self, on_success=self._on_login_success)

    def _on_login_success(self, org):
        self._org = org
        self._show_main()

    # ── Main layout ─────────────────────────────────────────
    def _show_main(self):
        self._clear()
        self.title(f"PockiTrack — {self._org.get('org_name', '')}")

        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        sidebar = Sidebar(
            root, self._org,
            on_navigate=self._navigate,
            on_logout=self._logout,
        )
        sidebar.pack(side="left", fill="y")

        self._content_area = tk.Frame(
            root, bg="white",
            highlightbackground="#E0E0E0",
            highlightthickness=0,
        )
        self._content_area.pack(side="left", fill="both", expand=True,
                                padx=20, pady=20)

        self._tabs = {
            "home":    HomeTab(   self._content_area, self._org, supabase),
            "history": HistoryTab(self._content_area, self._org),
            "wallets": WalletsTab(self._content_area, self._org),
            "profile": ProfileTab(self._content_area, self._org),
        }

        for t in self._tabs.values():
            t.pack_forget()

        self._sidebar = sidebar
        self._sidebar.set_active("home")   # triggers _navigate("home")

    def _navigate(self, key):
        for t in self._tabs.values():
            t.pack_forget()
        self._tabs[key].pack(fill="both", expand=True)

        # Reload fresh data on every tab switch
        if key == "history":
            self._tabs[key].load()
        elif key == "wallets":
            self._tabs[key].load_folders()
        elif key == "profile":
            self._tabs[key].load()

    def _logout(self):
        if messagebox.askyesno("Logout", "Log out of PockiTrack?"):
            self._org = None
            self.title("PockiTrack")
            self._show_start()


if __name__ == "__main__":
    app = PockiTrackApp()
    app.mainloop()