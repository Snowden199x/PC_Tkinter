import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
start_screen.py  –  PockiTrack landing page
Self-contained: no widgets.py needed.
PillButton defined here. Poppins loaded from system or fonts/ folder.

Sections (scrollable, top→bottom):
  1. Header   – logo left | Log In pill-button right
  2. Hero     – text left | white card right (2 wallet rows + progress bar)
  3. Features – centred heading + 4 feature boxes (amber shadow)
  4. CTA      – full-width amber banner + "Access your account" pill
  5. Footer   – dev credits + copyright
"""

import tkinter as tk
import tkinter.font as tkfont
import os
from PIL import Image, ImageTk

# ── paths ─────────────────────────────────────────────────────────────────────
_HERE      = _os.path.dirname(_os.path.abspath(__file__))
_BASE      = _os.path.dirname(_HERE)          # tkinter/
_ASSETS    = _os.path.join(_BASE, "assets", "images")
_FONTS_DIR = _os.path.join(_BASE, "fonts")   # optional Poppins .ttf location

# ── colours (straight from your CSS) ─────────────────────────────────────────
_BG          = "#f7f3eb"   # body
_HERO_BG     = "#fdf6e3"   # hero section  ≈ rgba(243,213,141,0.2) on cream
_WHITE       = "#ffffff"
_PRIMARY     = "#8b3b08"   # brown buttons
_PRIMARY_HOV = "#602805"   # hover
_AMBER       = "#e59e2c"   # income/expense text, info colour
_CARD_BDR    = "#f3d58d"   # hero-card border + shadow, feature shadow
_CTA_BG      = "#f3d58d"   # cta background
_TEXT_DARK   = "#2b2b2b"
_TEXT_MUTED  = "#828282"
_TEXT_BODY   = "#000000"
_FOOTER_MAIN = "#4A3B00"
_FOOTER_SUB  = "#6B5C2E"
_PROG_TRACK  = "#d9d9d9"
_CARD_INNER  = "#d9d9d9"   # inner wallet card border

# ── Poppins font ──────────────────────────────────────────────────────────────
def _load_poppins(root):
    """
    Try to register Poppins from fonts/ folder using Tk's font loading.
    Falls back gracefully to any available sans-serif.
    Returns the family name to use in font tuples.
    """
    # 1. already installed system-wide?
    families = tkfont.families(root)
    if "Poppins" in families:
        return "Poppins"

    # 2. try loading from fonts/ directory (needs Tk 8.6+ on Windows/Linux)
    if _os.path.isdir(_FONTS_DIR):
        for fname in _os.listdir(_FONTS_DIR):
            if fname.lower().startswith("poppins") and \
               fname.lower().endswith((".ttf", ".otf")):
                fpath = _os.path.join(_FONTS_DIR, fname)
                try:
                    # Tk's private font-load command (works on Windows & most Linux)
                    root.tk.call("font", "create", "PoppinsLoad")
                except Exception:
                    pass
                try:
                    root.tk.call("load", "", "Img")   # no-op if not present
                except Exception:
                    pass
                try:
                    # Tkinter ≥ 8.6 on Windows: use GDI font registration
                    import ctypes
                    ctypes.windll.gdi32.AddFontResourceExW(fpath, 0x10, 0)
                    root.tk.call("font", "families")  # refresh cache
                    if "Poppins" in tkfont.families(root):
                        return "Poppins"
                except Exception:
                    pass

    # 3. fallback chain
    for fam in ("Segoe UI", "Helvetica Neue", "Arial"):
        if fam in families:
            return fam
    return "Arial"


def _f(family, size, weight="normal"):
    """Return a Tkinter font tuple."""
    return (family, size, weight)


# ── PillButton ────────────────────────────────────────────────────────────────
class PillButton(tk.Canvas):
    """
    Canvas-drawn pill-shaped button with full hover support.

    Parameters
    ----------
    parent       : tk widget
    text         : button label
    width/height : dimensions in px
    bg           : normal background colour
    fg           : normal text colour
    hover_bg     : background on mouse-over
    hover_fg     : text colour on mouse-over
    border_color : if given, draws a 2-px outline ring
    font         : tkinter font tuple  e.g. ("Poppins", 11, "bold")
    radius       : corner radius – defaults to height//2 (true pill)
    command      : callable
    """
    def __init__(self, parent,
                 text="",
                 width=130, height=40,
                 bg="#8b3b08", fg="#ffffff",
                 hover_bg="#602805", hover_fg="#ffffff",
                 border_color=None,
                 font=None,
                 radius=None,
                 command=None,
                 **kw):

        # canvas background must match parent so clipped corners look invisible
        try:
            pbg = parent["bg"]
        except Exception:
            pbg = _BG

        super().__init__(parent,
                         width=width, height=height,
                         bd=0, highlightthickness=0,
                         bg=pbg, cursor="hand2", **kw)

        self._text     = text
        self._bg       = bg
        self._fg       = fg
        self._hbg      = hover_bg
        self._hfg      = hover_fg
        self._border   = border_color
        self._font     = font or ("Arial", 10, "bold")
        self._radius   = radius          # None → computed in _draw
        self._cmd      = command
        self._cur_bg   = bg
        self._cur_fg   = fg

        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>",     self._enter)
        self.bind("<Leave>",     self._leave)
        self.bind("<Button-1>",  self._click)
        self._draw()

    # ── internals ────────────────────────────────────────────────────
    def _pill(self, x1, y1, x2, y2, r, **kw):
        """Draw a smooth rounded rectangle (pill shape) on self."""
        pts = [
            x1+r, y1,    x2-r, y1,
            x2,   y1,    x2,   y1+r,
            x2,   y2-r,  x2,   y2,
            x2-r, y2,    x1+r, y2,
            x1,   y2,    x1,   y2-r,
            x1,   y1+r,  x1,   y1,
            x1+r, y1,
        ]
        return self.create_polygon(pts, smooth=True, **kw)

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()  or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        r = self._radius if self._radius is not None else h // 2
        r = min(r, w // 2, h // 2)

        if self._border:
            # outer border ring
            self._pill(0, 0, w, h, r,
                       fill=self._border, outline="")
            # inner fill
            self._pill(2, 2, w-2, h-2, max(r-2, 2),
                       fill=self._cur_bg, outline="")
        else:
            self._pill(0, 0, w, h, r,
                       fill=self._cur_bg, outline="")

        self.create_text(w // 2, h // 2,
                         text=self._text,
                         fill=self._cur_fg,
                         font=self._font)

    def _enter(self, _):
        self._cur_bg, self._cur_fg = self._hbg, self._hfg
        self._draw()

    def _leave(self, _):
        self._cur_bg, self._cur_fg = self._bg, self._fg
        self._draw()

    def _click(self, _):
        if self._cmd:
            self._cmd()

    def set_text(self, text):
        self._text = text
        self._draw()


# ══════════════════════════════════════════════════════════════════════════════
# StartScreen
# ══════════════════════════════════════════════════════════════════════════════
class StartScreen(tk.Frame):
    def __init__(self, parent, on_login, **kw):
        super().__init__(parent, bg=_BG, **kw)
        self._on_login = on_login
        self._imgs     = []   # keep PhotoImage refs alive

        # load Poppins (or best fallback) once
        root = self.winfo_toplevel()
        self._fam = _load_poppins(root)

        self._build()

    # ── font shorthand ────────────────────────────────────────────────
    def _f(self, size, weight="normal"):
        return (self._fam, size, weight)

    # ── scrollable page scaffold ──────────────────────────────────────
    def _build(self):
        self._cv = tk.Canvas(self, bg=_BG, bd=0, highlightthickness=0)
        vsb = tk.Scrollbar(self, orient="vertical", command=self._cv.yview)
        self._cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._cv.pack(side="left", fill="both", expand=True)

        self._pg = tk.Frame(self._cv, bg=_BG)
        self._wid = self._cv.create_window((0, 0), window=self._pg, anchor="nw")

        self._cv.bind("<Configure>",
            lambda e: self._cv.itemconfig(self._wid, width=e.width))
        self._pg.bind("<Configure>",
            lambda e: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._cv.bind_all("<MouseWheel>",
            lambda e: self._cv.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._header()
        self._hero()
        self._features()
        self._cta()
        self._footer()

    # ══════════════════════════════════════════════════════════════════
    # 1. HEADER
    #    background: #f7f3eb   padding: 15px 50px
    #    logo left  (img 90px + bold name 34px)
    #    login-btn right  (bg #8b3b08, white text, radius 10px, 12px 35px pad)
    # ══════════════════════════════════════════════════════════════════
    def _header(self):
        hdr = tk.Frame(self._pg, bg=_BG)
        hdr.pack(fill="x", padx=50, pady=15)

        # ── logo ─────────────────────────────────────────────────────
        lf = tk.Frame(hdr, bg=_BG, cursor="hand2")
        lf.pack(side="left")

        logo_ico = self._img("pocki_logo.png", 64, base=True)
        if logo_ico:
            tk.Label(lf, image=logo_ico, bg=_BG).pack(side="left")

        tk.Label(lf, text="PockiTrack",
                 bg=_BG, fg=_TEXT_BODY,
                 font=self._f(22, "bold")).pack(side="left", padx=12)

        # ── Log In pill button ────────────────────────────────────────
        # CSS: bg #8b3b08, white text, border-radius 10px, padding 12px 35px
        PillButton(hdr,
                   text="Log in",
                   width=120, height=42,
                   bg=_PRIMARY, fg=_WHITE,
                   hover_bg=_PRIMARY_HOV, hover_fg=_WHITE,
                   border_color=None,
                   radius=10,
                   font=self._f(12, "bold"),
                   command=self._on_login).pack(side="right")

    # ══════════════════════════════════════════════════════════════════
    # 2. HERO
    #    bg: rgba(243,213,141,0.2) ≈ #fdf6e3    padding: 80px 100px
    #    LEFT  – h1 (40px weight-500), p (#828282), get-started btn
    #    RIGHT – .hero-card  width 640 height 380  border #f3d58d
    #              box-shadow 0 4 12 3 #f3d58d   border-radius 25px
    #              two .card rows  (wallet icon + progress bar)
    # ══════════════════════════════════════════════════════════════════
    def _hero(self):
        hero = tk.Frame(self._pg, bg=_HERO_BG)
        hero.pack(fill="x")

        inner = tk.Frame(hero, bg=_HERO_BG)
        inner.pack(padx=80, pady=60, fill="x")

        # ── LEFT: hero text ───────────────────────────────────────────
        left = tk.Frame(inner, bg=_HERO_BG)
        left.pack(side="left", anchor="n", fill="y")

        tk.Label(left,
                 text="Financial Management\nMade Simple",
                 bg=_HERO_BG, fg=_TEXT_BODY,
                 font=self._f(28),          # CSS: 40px weight-500
                 justify="left").pack(anchor="w")

        tk.Label(left,
                 text=("PockiTrack helps university organizations track\n"
                       "expenses, manage budgets, and generate\n"
                       "professional financial reports with ease."),
                 bg=_HERO_BG, fg=_TEXT_MUTED,
                 font=self._f(10),
                 justify="left").pack(anchor="w", pady=20)

        # CSS: get-started  bg #8b3b08 white text  border-radius 8px
        #      font-size 20px font-weight 600  padding 12px 25px
        PillButton(left,
                   text="Get started →",
                   width=175, height=44,
                   bg=_PRIMARY, fg=_WHITE,
                   hover_bg=_PRIMARY_HOV, hover_fg=_WHITE,
                   radius=8,
                   font=self._f(13, "bold"),
                   command=self._on_login).pack(anchor="w")

        # ── RIGHT: hero card ──────────────────────────────────────────
        right = tk.Frame(inner, bg=_HERO_BG)
        right.pack(side="right", anchor="n", padx=(50, 0))
        self._hero_card(right)

    # ── hero card (canvas for rounded corners + shadow illusion) ──────
    def _hero_card(self, parent):
        """
        CSS: width 640  height 380  bg white  border 1px #f3d58d
             box-shadow 0 4 12 3 #f3d58d   border-radius 25px
        We fake the shadow with a slightly larger amber frame behind.
        """
        # shadow layer
        shadow = tk.Frame(parent, bg=_CARD_BDR, padx=4, pady=4)
        shadow.pack()

        # white card
        card = tk.Frame(shadow, bg=_WHITE, padx=28, pady=22)
        card.pack()

        wallets = [
            ("SEMINAR",          70,  "Income: Php 5,000",  "Expenses: Php 3,500"),
            ("OUTREACH PROGRAM", 40,  "Income: Php 3,000",  "Expenses: Php 1,200"),
        ]
        for i, (name, pct, inc, exp) in enumerate(wallets):
            if i:
                # divider between rows
                tk.Frame(card, bg=_CARD_INNER, height=1).pack(
                    fill="x", pady=10)
            self._wallet_row(card, name, pct, inc, exp)

    def _wallet_row(self, parent, name, pct, inc_txt, exp_txt):
        """
        CSS .card:  display flex  align-items center  gap 25px
                    min-height 150  border-radius 12  border 1px #d9d9d9
                    padding 20 25
        """
        row = tk.Frame(parent, bg=_WHITE,
                       highlightbackground=_CARD_INNER,
                       highlightthickness=1,
                       pady=18, padx=20)
        row.pack(fill="x", pady=4)

        # wallet icon  CSS: width/height 95px  border-radius 12px
        ico = self._img("wallet.png", 80)
        if ico:
            tk.Label(row, image=ico, bg=_WHITE).pack(side="left")
        else:
            tk.Label(row, text="💼", bg=_WHITE,
                     font=self._f(28)).pack(side="left")

        det = tk.Frame(row, bg=_WHITE)
        det.pack(side="left", fill="x", expand=True, padx=(22, 0))

        # CSS .card-details h4: font-size 18px  font-weight 600
        tk.Label(det, text=name, bg=_WHITE, fg=_TEXT_BODY,
                 font=self._f(12, "bold"), anchor="w").pack(anchor="w")

        # CSS .budget: font-size 16px  color #333
        tk.Label(det, text="Budget Used", bg=_WHITE, fg="#333333",
                 font=self._f(10), anchor="w").pack(anchor="w")

        # progress bar  CSS: height 14px  bg rgba(217,217,217,0.3)
        pb = tk.Canvas(det, height=14, bg=_PROG_TRACK,
                       bd=0, highlightthickness=0)
        pb.pack(fill="x", pady=10)
        pb.bind("<Configure>",
                lambda e, c=pb, p=pct: self._draw_pb(c, p))

        # CSS .info: font-size 16px  color #e59e2c  gap 70px
        info = tk.Frame(det, bg=_WHITE)
        info.pack(anchor="w")
        tk.Label(info, text=inc_txt, bg=_WHITE,
                 fg=_AMBER, font=self._f(10, "bold")).pack(side="left")
        tk.Label(info, text="          ", bg=_WHITE).pack(side="left")
        tk.Label(info, text=exp_txt, bg=_WHITE,
                 fg=_AMBER, font=self._f(10, "bold")).pack(side="left")

    def _draw_pb(self, canvas, pct):
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 4: return
        r = h // 2
        # track
        self._pill_canvas(canvas, 0, 0, w, h, r, _PROG_TRACK)
        # fill
        filled = max(r * 2, int(w * pct / 100))
        self._pill_canvas(canvas, 0, 0, filled, h, r, _PRIMARY)

    @staticmethod
    def _pill_canvas(canvas, x1, y1, x2, y2, r, colour):
        pts = [
            x1+r, y1,   x2-r, y1,
            x2,   y1,   x2,   y1+r,
            x2,   y2-r, x2,   y2,
            x2-r, y2,   x1+r, y2,
            x1,   y2,   x1,   y2-r,
            x1,   y1+r, x1,   y1,
            x1+r, y1,
        ]
        canvas.create_polygon(pts, smooth=True, fill=colour, outline="")

    # ══════════════════════════════════════════════════════════════════
    # 3. FEATURES
    #    padding: 80px 60px   text-align center
    #    h2: 40px weight-500   p: #828282
    #    .features-grid: flex  gap 20  margin-top 120
    #    .feature-box: bg white  shadow rgba(243,213,141,.36)
    #                  border-radius 12  310×312  padding 25
    #                  hover: translateY(-5px)
    # ══════════════════════════════════════════════════════════════════
    def _features(self):
        sec = tk.Frame(self._pg, bg=_BG)
        sec.pack(fill="x", padx=60, pady=60)

        tk.Label(sec,
                 text="Everything You Need to Manage Your Finances",
                 bg=_BG, fg=_TEXT_BODY,
                 font=self._f(22)).pack()          # CSS 40px → ~22pt

        tk.Label(sec,
                 text=("Built specifically for student organizations to meet "
                       "university financial reporting requirements."),
                 bg=_BG, fg=_TEXT_MUTED,
                 font=self._f(9)).pack(pady=(4, 36))

        grid = tk.Frame(sec, bg=_BG)
        grid.pack()

        items = [
            ("track_finances.png",   "Track Finances",
             "Monitor your organization's income, expenses, and budget\n"
             "in real-time with intuitive dashboards."),
            ("generate_reports.png", "Generate Reports",
             "Create professional Event, Monthly, and Summary Financial\n"
             "Reports formatted for school requirements."),
            ("secured.png",          "Secure & Reliable",
             "Keep your financial data safe with secure authentication\n"
             "and organized record-keeping."),
            ("collaborate.png",      "Multi-Officer Access",
             "Designed for Presidents, VPs, Treasurers, and Auditors\n"
             "to collaborate on financial management."),
        ]
        for col, (icon, title, desc) in enumerate(items):
            self._feature_box(grid, col, icon, title, desc)

    def _feature_box(self, parent, col, icon_file, title, desc):
        """
        CSS .feature-box: bg white  box-shadow 0 4 8.2 3 rgba(243,213,141,.36)
            border-radius 12  width 310  height 312  padding 25
        We fake shadow with an amber backing frame.
        """
        # amber shadow frame
        shadow = tk.Frame(parent, bg=_CARD_BDR, padx=3, pady=4)
        shadow.grid(row=0, column=col, padx=10, pady=8, sticky="nsew")

        card = tk.Frame(shadow, bg=_WHITE,
                        padx=24, pady=24,
                        width=248, height=280)
        card.pack(fill="both", expand=True)
        card.pack_propagate(False)

        # hover lift effect
        def _enter(e):
            shadow.config(pady=0)
        def _leave(e):
            shadow.config(pady=4)
        card.bind("<Enter>", _enter)
        card.bind("<Leave>", _leave)

        # CSS .feature-icon: 68×68
        ico = self._img(icon_file, 60)
        if ico:
            tk.Label(card, image=ico, bg=_WHITE).pack(
                anchor="w", pady=(0, 16))
        else:
            tk.Label(card, text="●", bg=_WHITE,
                     fg=_PRIMARY, font=self._f(24)).pack(anchor="w")

        # CSS h3: 18px weight-600
        tk.Label(card, text=title, bg=_WHITE, fg=_TEXT_BODY,
                 font=self._f(11, "bold"), anchor="w").pack(anchor="w")

        # CSS p: 14px  opacity 0.8
        tk.Label(card, text=desc, bg=_WHITE, fg="#333333",
                 font=self._f(8), justify="left", anchor="w",
                 wraplength=215).pack(anchor="w", pady=(8, 0))

    # ══════════════════════════════════════════════════════════════════
    # 4. CTA
    #    CSS: bg #f3d58d  box-shadow …  border-radius 20  margin 80 auto
    #         width 1330  height 350  flex center
    #         h3: 40px weight-500   p: 16px opacity 0.8
    #         .access-btn: bg #8b3b08 white  font-weight 600
    #                      padding 14 30  border-radius 8
    # ══════════════════════════════════════════════════════════════════
    def _cta(self):
        outer = tk.Frame(self._pg, bg=_BG)
        outer.pack(fill="x", padx=50, pady=50)

        # amber card with slight rounded look via border frame
        cta = tk.Frame(outer, bg=_CTA_BG, pady=55, padx=50)
        cta.pack(fill="x")

        tk.Label(cta,
                 text="Ready to Simplify Your Organization's Finances?",
                 bg=_CTA_BG, fg=_TEXT_BODY,
                 font=self._f(22)).pack()      # CSS 40px weight-500

        tk.Label(cta,
                 text=("Get started with PockiTrack today and manage "
                       "your finances with confidence."),
                 bg=_CTA_BG, fg=_TEXT_BODY,
                 font=self._f(10)).pack(pady=(10, 24))

        # CSS: bg #8b3b08  white  border-radius 8  padding 14 30
        PillButton(cta,
                   text="Access your account",
                   width=210, height=44,
                   bg=_PRIMARY, fg=_WHITE,
                   hover_bg=_PRIMARY_HOV, hover_fg=_WHITE,
                   radius=8,
                   font=self._f(11, "bold"),
                   command=self._on_login).pack()

    # ══════════════════════════════════════════════════════════════════
    # 5. FOOTER
    #    CSS: border-top 1px rgba(0,0,0,0.1)  padding 10px
    #         .footer-text: 12px  color #4A3B00
    #         .footer-credit: 12px  color #6B5C2E  opacity 0.8
    # ══════════════════════════════════════════════════════════════════
    def _footer(self):
        tk.Frame(self._pg, bg="#e0d8cc", height=1).pack(fill="x")

        footer = tk.Frame(self._pg, bg=_BG, pady=10)
        footer.pack(fill="x")

        tk.Label(footer,
                 text=("Developed by  Snowden,  Yngrie,  and  Zoo\n"
                       "from Laguna State Polytechnic University – Sta. Cruz Campus"),
                 bg=_BG, fg=_FOOTER_MAIN,
                 font=self._f(8)).pack()

        tk.Label(footer,
                 text="© 2025 PockiTrack. All rights reserved.",
                 bg=_BG, fg=_FOOTER_SUB,
                 font=self._f(8)).pack()

    # ── image loader ──────────────────────────────────────────────────
    def _img(self, filename, size, base=False):
        path = _os.path.join(_BASE if base else _ASSETS, filename)
        if not _os.path.exists(path):
            return None
        try:
            img = Image.open(path).resize((size, size), Image.LANCZOS)
            ph  = ImageTk.PhotoImage(img)
            self._imgs.append(ph)   # prevent GC
            return ph
        except Exception:
            return None