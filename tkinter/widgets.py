"""
widgets.py – reusable styled widgets for PockiTrack
"""
import tkinter as tk
from tkinter import ttk
from constants import *


# ─────────────────────────────────────────────────────────────────────────────
# Rounded-rectangle helper (drawn on a Canvas)
# ─────────────────────────────────────────────────────────────────────────────

def rounded_rect(canvas, x1, y1, x2, y2, r=12, **kwargs):
    """Draw a rounded rectangle on *canvas* and return the item id list."""
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# RoundedFrame  – a Frame that looks like a rounded card
# ─────────────────────────────────────────────────────────────────────────────

class RoundedFrame(tk.Canvas):
    """A canvas that draws a rounded-rectangle card behind its children."""

    def __init__(self, parent, radius=CORNER_R, bg=BG_CARD,
                 border_color=DIVIDER, border_width=1, **kwargs):
        super().__init__(parent, bd=0, highlightthickness=0,
                         relief="flat", **kwargs)
        self._radius = radius
        self._fill   = bg
        self._border = border_color
        self._bw     = border_width
        self._rect   = None
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2 or h < 2:
            return
        bw = self._bw
        if self._border and bw:
            rounded_rect(self, 0, 0, w, h, self._radius,
                         fill=self._border, outline="", tags="bg")
            rounded_rect(self, bw, bw, w-bw, h-bw, self._radius-1,
                         fill=self._fill, outline="", tags="bg")
        else:
            rounded_rect(self, 0, 0, w, h, self._radius,
                         fill=self._fill, outline="", tags="bg")
        self.tag_lower("bg")

    def configure(self, **kw):
        if "bg" in kw:
            self._fill = kw.pop("bg")
            self._redraw()
        super().configure(**kw)


# ─────────────────────────────────────────────────────────────────────────────
# PillButton  (also aliased as RoundedButton for backwards compat)
# Matches the PillButton pattern: bg, fg, hover_bg, hover_fg,
# border_color, font, width, height, radius, command
# ─────────────────────────────────────────────────────────────────────────────

class PillButton(tk.Canvas):
    """
    Canvas-drawn pill / rounded-rectangle button.

    Parameters mirror the PillButton API seen in the codebase:
        bg, fg               – normal fill & text colour
        hover_bg, hover_fg   – colours on mouse-over
        border_color         – outline colour (drawn as a 2-px ring)
        font                 – tkinter font tuple, e.g. (family, size, weight)
        width, height        – button dimensions in pixels
        radius               – corner radius (default = height//2 for true pill)
        command              – callable invoked on click
    """
    def __init__(self, parent,
                 text="",
                 width=120, height=40,
                 bg=PRIMARY, fg=BTN_TEXT,
                 hover_bg=None, hover_fg=None,
                 border_color=None,
                 radius=None,
                 font=None,
                 command=None,
                 **kwargs):

        # canvas bg must match the parent background so the rounded
        # corners look transparent
        try:
            parent_bg = parent["bg"]
        except Exception:
            parent_bg = BG_CREAM

        super().__init__(parent,
                         width=width, height=height,
                         bd=0, highlightthickness=0,
                         bg=parent_bg,
                         cursor="hand2", **kwargs)

        self._text        = text
        self._bg          = bg
        self._fg          = fg
        self._hover_bg    = hover_bg  if hover_bg  is not None else PRIMARY_DARK
        self._hover_fg    = hover_fg  if hover_fg  is not None else fg
        self._border      = border_color
        self._radius      = radius    if radius    is not None else height // 2
        self._font        = font      if font      is not None else \
                            (FONT_FAMILY, 10, "bold")
        self._cmd         = command
        self._current_bg  = bg
        self._current_fg  = fg

        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>",     self._on_enter)
        self.bind("<Leave>",     self._on_leave)
        self.bind("<Button-1>",  self._on_click)

        self._draw()

    # ── drawing ──────────────────────────────────────────────────────
    def _draw(self):
        self.delete("all")
        w = self.winfo_width()  or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        r = min(self._radius, w // 2, h // 2)

        # border ring (drawn first, slightly larger)
        if self._border:
            rounded_rect(self, 0, 0, w, h, r,
                         fill=self._border, outline="")
            rounded_rect(self, 2, 2, w-2, h-2, max(r-2, 2),
                         fill=self._current_bg, outline="")
        else:
            rounded_rect(self, 0, 0, w, h, r,
                         fill=self._current_bg, outline="")

        self.create_text(w // 2, h // 2,
                         text=self._text,
                         fill=self._current_fg,
                         font=self._font)

    # ── hover ────────────────────────────────────────────────────────
    def _on_enter(self, _e):
        self._current_bg = self._hover_bg
        self._current_fg = self._hover_fg
        self._draw()

    def _on_leave(self, _e):
        self._current_bg = self._bg
        self._current_fg = self._fg
        self._draw()

    def _on_click(self, _e):
        if self._cmd:
            self._cmd()

    # ── public API ───────────────────────────────────────────────────
    def configure(self, **kw):
        redraw = False
        for attr, internal in [("text",  "_text"),
                                ("bg",    "_bg"),
                                ("fg",    "_fg")]:
            if attr in kw:
                setattr(self, internal, kw.pop(attr))
                redraw = True
        if "command" in kw:
            self._cmd = kw.pop("command")
        super().configure(**kw)
        if redraw:
            self._current_bg = self._bg
            self._current_fg = self._fg
            self._draw()


# backwards-compat alias
RoundedButton = PillButton


# ─────────────────────────────────────────────────────────────────────────────
# SummaryCard  – the coloured stat tiles on Home / Wallet screens
# ─────────────────────────────────────────────────────────────────────────────

class SummaryCard(tk.Frame):
    def __init__(self, parent, label="", value="₱0.00",
                 bg=AMBER_BG, accent=AMBER, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.configure(padx=14, pady=10)

        # coloured left bar
        bar = tk.Frame(self, bg=accent, width=4)
        bar.pack(side="left", fill="y", padx=(0, 10))

        info = tk.Frame(self, bg=bg)
        info.pack(side="left", fill="both", expand=True)

        tk.Label(info, text=label, bg=bg,
                 fg=TEXT_MUTED, font=font(8)).pack(anchor="w")
        tk.Label(info, text=value, bg=bg,
                 fg=TEXT_DARK, font=font(13, "bold")).pack(anchor="w")


# ─────────────────────────────────────────────────────────────────────────────
# TransactionRow
# ─────────────────────────────────────────────────────────────────────────────

class TransactionRow(tk.Frame):
    def __init__(self, parent, date="", description="",
                 amount=0.0, category="", bg=BG_WHITE, **kwargs):
        super().__init__(parent, bg=bg, pady=6, **kwargs)

        sign  = "+" if amount >= 0 else "-"
        color = INCOME_GREEN if amount >= 0 else EXPENSE_RED
        amt   = f"{sign}₱{abs(amount):,.2f}"

        tk.Label(self, text=date, bg=bg,
                 fg=TEXT_MUTED, font=font(8),
                 width=10, anchor="w").pack(side="left")
        tk.Label(self, text=description, bg=bg,
                 fg=TEXT_DARK, font=font(9),
                 anchor="w").pack(side="left", expand=True, fill="x")
        tk.Label(self, text=category, bg=bg,
                 fg=TEXT_MUTED, font=font(8),
                 width=12, anchor="w").pack(side="left")
        tk.Label(self, text=amt, bg=bg,
                 fg=color, font=font(9, "bold"),
                 width=12, anchor="e").pack(side="right")

        sep = tk.Frame(self, bg=DIVIDER, height=1)
        sep.pack(side="bottom", fill="x")


# ─────────────────────────────────────────────────────────────────────────────
# StyledEntry  – rounded-looking entry field
# ─────────────────────────────────────────────────────────────────────────────

class StyledEntry(tk.Frame):
    """Entry wrapped in a rounded-looking frame."""
    def __init__(self, parent, placeholder="", show="", **kwargs):
        super().__init__(parent, bg=DIVIDER, padx=1, pady=1,
                         highlightthickness=0, **kwargs)
        inner = tk.Frame(self, bg=BG_WHITE)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        self._ph   = placeholder
        self._show = show
        self.var   = tk.StringVar()

        self.entry = tk.Entry(inner, textvariable=self.var,
                              font=font(10), bg=BG_WHITE, fg=TEXT_DARK,
                              bd=0, highlightthickness=0,
                              insertbackground=TEXT_DARK, show=show)
        self.entry.pack(padx=10, pady=8, fill="x")

        if placeholder:
            self._add_placeholder()

    def _add_placeholder(self):
        self.entry.insert(0, self._ph)
        self.entry.config(fg=TEXT_MUTED)
        self.entry.bind("<FocusIn>",  self._clear_ph)
        self.entry.bind("<FocusOut>", self._restore_ph)

    def _clear_ph(self, e):
        if self.entry.get() == self._ph:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT_DARK,
                              show=self._show if self._show else "")

    def _restore_ph(self, e):
        if not self.entry.get():
            self.entry.config(fg=TEXT_MUTED, show="")
            self.entry.insert(0, self._ph)

    def get(self):
        val = self.entry.get()
        return "" if val == self._ph else val


# ─────────────────────────────────────────────────────────────────────────────
# Scrollable frame helper
# ─────────────────────────────────────────────────────────────────────────────

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg=BG_WHITE, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical",
                                  command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=bg)
        self.inner.bind("<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(
                int(-1*(e.delta/120)), "units"))