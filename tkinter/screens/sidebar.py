import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
"""
sidebar.py – left navigation rail for PockiTrack
"""
import tkinter as tk
from constants import *
import os
from PIL import Image, ImageTk


ICON_NAMES = {
    "home":    "dashboard_menu",
    "history": "navi_history",
    "wallet":  "navi_wallet",
    "profile": "navi_profile",
}

NAV_ITEMS = [
    ("home",    "Home"),
    ("history", "History"),
    ("wallet",  "Wallet"),
    ("profile", "Profile"),
]


def _load_icon(name, size=24):
    """Return a PhotoImage for *name* from assets, or None."""
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA").resize(
            (size, size), Image.LANCZOS)
        # tint white for dark sidebar
        r, g, b, a = img.split()
        white = Image.new("RGB", img.size, (255, 255, 255))
        white.putalpha(a)
        return ImageTk.PhotoImage(white)
    except Exception:
        return None


class Sidebar(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=SIDEBAR_BG,
                         width=SIDEBAR_W, **kwargs)
        self.pack_propagate(False)
        self._on_nav  = on_navigate
        self._active  = "home"
        self._buttons = {}
        self._icons   = {}

        # ── Logo ────────────────────────────────────────────────────
        logo_path = os.path.join(BASE_DIR, "pocki_logo.png")
        self._logo_img = None
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize((38, 38), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
            except Exception:
                pass

        logo_frame = tk.Frame(self, bg=SIDEBAR_BG, pady=18)
        logo_frame.pack(fill="x")
        if self._logo_img:
            tk.Label(logo_frame, image=self._logo_img,
                     bg=SIDEBAR_BG).pack()
        else:
            tk.Label(logo_frame, text="P", bg=AMBER,
                     fg=BTN_TEXT, font=font(16, "bold"),
                     width=2, height=1).pack()

        # ── Nav items ────────────────────────────────────────────────
        nav_frame = tk.Frame(self, bg=SIDEBAR_BG)
        nav_frame.pack(fill="both", expand=True, pady=10)

        for key, label in NAV_ITEMS:
            icon_name = ICON_NAMES.get(key, key)
            ico = _load_icon(icon_name, 22)
            self._icons[key] = ico          # keep reference
            btn = self._make_nav_btn(nav_frame, key, label, ico)
            self._buttons[key] = btn

        # ── Logout at bottom ─────────────────────────────────────────
        logout_ico = _load_icon("logout_icon", 22)
        self._icons["logout"] = logout_ico
        self._icons["logout"] = logout_ico
        bottom = tk.Frame(self, bg=SIDEBAR_BG, pady=14)
        bottom.pack(fill="x", side="bottom")
        self._make_nav_btn(bottom, "logout", "Log out",
                           logout_ico, is_logout=True)

        self.set_active("home")

    # ── builder ──────────────────────────────────────────────────────
    def _make_nav_btn(self, parent, key, label, icon=None,
                      is_logout=False):
        frame = tk.Frame(parent, bg=SIDEBAR_BG,
                         cursor="hand2", pady=6)
        frame.pack(fill="x", padx=6, pady=2)

        if icon:
            lbl = tk.Label(frame, image=icon, bg=SIDEBAR_BG)
        else:
            # fallback: first letter
            lbl = tk.Label(frame, text=label[0], bg=SIDEBAR_BG,
                           fg="white", font=font(11, "bold"))
        lbl.pack()

        tip = tk.Label(frame, text=label, bg=SIDEBAR_BG,
                       fg=TEXT_MUTED, font=font(7))
        tip.pack()

        def _click(e=None):
            if is_logout:
                self._on_nav("logout")
            else:
                self.set_active(key)
                self._on_nav(key)

        for w in (frame, lbl, tip):
            w.bind("<Button-1>", _click)
            if not is_logout:
                w.bind("<Enter>", lambda e, f=frame: self._hover(f, True))
                w.bind("<Leave>", lambda e, f=frame: self._hover(f, False))

        frame._key = key
        frame._icon_lbl = lbl
        frame._tip_lbl  = tip
        return frame

    def _hover(self, frame, entering):
        if frame._key == self._active:
            return
        c = "#4A2510" if entering else SIDEBAR_BG
        frame.config(bg=c)
        frame._icon_lbl.config(bg=c)
        frame._tip_lbl.config(bg=c)

    def set_active(self, key):
        # reset old
        if self._active in self._buttons:
            old = self._buttons[self._active]
            old.config(bg=SIDEBAR_BG)
            old._icon_lbl.config(bg=SIDEBAR_BG)
            old._tip_lbl.config(fg=TEXT_MUTED)
        self._active = key
        if key in self._buttons:
            btn = self._buttons[key]
            btn.config(bg=SIDEBAR_ACTIVE)
            btn._icon_lbl.config(bg=SIDEBAR_ACTIVE)
            btn._tip_lbl.config(fg="white")
