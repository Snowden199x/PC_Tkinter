# PockiTrack Constants
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "images")

# ── Colors ────────────────────────────────────────────────────────────────────
BG_CREAM       = "#F5F0E6"      # main background
BG_WHITE       = "#FFFFFF"
BG_CARD        = "#FDFAF4"      # card / panel background
SIDEBAR_BG     = "#3B1F0E"      # dark brown sidebar
SIDEBAR_ACTIVE = "#6B3A1F"      # active nav item
PRIMARY        = "#7B3F1A"      # primary brown
PRIMARY_DARK   = "#5A2D0C"
AMBER          = "#C4872A"      # golden amber accent
AMBER_LIGHT    = "#E8A84C"
AMBER_BG       = "#FFF3DC"      # very light amber (summary cards)
BTN_TEXT       = "#FFFFFF"
TEXT_DARK      = "#2C1A0E"
TEXT_MUTED     = "#9A8070"
TEXT_LABEL     = "#6B5040"
DIVIDER        = "#E8DECE"
INCOME_GREEN   = "#4CAF79"
EXPENSE_RED    = "#E05C5C"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_FAMILY    = "Poppins"
FONT_FALLBACK  = ("Poppins", "Segoe UI", "Arial")   # tkinter font tuple fallback

def font(size=11, weight="normal", family=FONT_FAMILY):
    """Return a tkinter-compatible font tuple."""
    return (family, size, weight)

# ── Dimensions ────────────────────────────────────────────────────────────────
SIDEBAR_W      = 220
WINDOW_W       = 1100
WINDOW_H       = 680
CORNER_R       = 14            # general card radius (for canvas-drawn widgets)
BTN_R          = 10

# ── App info ──────────────────────────────────────────────────────────────────
APP_NAME       = "PockiTrack"
