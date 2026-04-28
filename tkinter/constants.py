"""
constants.py — Shared design tokens, style helpers, supabase client, and icon loader.
Import this in every screen file.
"""

import os
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ─────────────────────────────────────────
# SUPABASE CLIENT
# ─────────────────────────────────────────
_supabase_url = os.getenv("SUPABASE_URL")
_supabase_key = os.getenv("SUPABASE_KEY")

if not _supabase_url or not _supabase_key:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_KEY in .env file.\n"
        "Make sure your .env file is in the same folder as main.py."
    )

supabase = create_client(_supabase_url, _supabase_key)

# ─────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────
BG          = "#F5F1E8"
WHITE       = "#FFFFFF"
ACTIVE_NAV  = "#A24A00"
AMBER       = "#E59E2C"
AMBER_LIGHT = "#F3D58D"
AMBER_MID   = "#ECB95D"
CREAM       = "#ECDDC6"
TEXT_DARK   = "#000000"
TEXT_MUTE   = "#616161"
TEXT_GRAY   = "#828282"
GREEN_OK    = "#2E7D32"
RED_ERR     = "#C62828"
CARD_GLASS  = "#F8EDD4"

FONT_MAIN:  tuple = ("Poppins", 10)
FONT_BOLD:  tuple = ("Poppins", 10, "bold")
FONT_TITLE: tuple = ("Georgia", 22, "italic")

MONTH_KEYS = [
    "august","september","october","november","december",
    "january","february","march","april","may",
]
MONTH_LABELS = {k: k.capitalize() for k in MONTH_KEYS}

# ─────────────────────────────────────────
# STYLE HELPERS
# ─────────────────────────────────────────
def styled_btn(parent, text, cmd, bg=ACTIVE_NAV, fg=WHITE, font=FONT_MAIN, **kw):
    return tk.Button(
        parent, text=text, command=cmd, bg=bg, fg=fg,
        font=font, relief="flat", cursor="hand2",
        activebackground=AMBER, activeforeground=WHITE,
        padx=14, pady=6, **kw
    )

def section_label(parent, text, **kw):
    return tk.Label(parent, text=text, bg=BG, fg=TEXT_DARK,
                    font=("Poppins", 9), **kw)

def card_frame(parent, **kw):
    return tk.Frame(parent, bg=WHITE, relief="flat",
                    highlightbackground=CREAM,
                    highlightthickness=1, **kw)

# ─────────────────────────────────────────
# ICON LOADER
# ─────────────────────────────────────────
_icon_cache = {}

def load_icon(path, size=(20, 20)):
    key = (path, size)
    if key in _icon_cache:
        return _icon_cache[key]
    if PIL_OK and os.path.exists(path):
        img = Image.open(path).resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        _icon_cache[key] = photo
        return photo
    return None