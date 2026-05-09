import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from constants import *
from PIL import Image, ImageTk

# ── colours matching the web CSS ─────────────────────────────────────────────
_BG          = "#F5F1E8"   # sidebar / page background
_NAV_FG      = "#616161"   # inactive label colour
_NAV_ACTIVE  = "#A24A00"   # active pill background
_NAV_HOVER   = "#ECDDC6"   # hover pill background
_LOGOUT_BG   = "#FFFFFF"   # logout button background
_LOGOUT_FG   = "#616161"

NAV_ITEMS = [
    ("home",    "Home",    "dashboard_menu.png"),
    ("history", "History", "navi_history.png"),
    ("wallet",  "Wallets", "navi_wallet.png"),
    ("profile", "Profile", "navi_profile.png"),
]


def _load(path, w, h, tint=None):
    """Load & resize an image; optionally tint to a solid colour."""
    if not _os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA").resize((w, h), Image.LANCZOS)
        if tint:
            r, g, b = int(tint[1:3], 16), int(tint[3:5], 16), int(tint[5:7], 16)
            coloured = Image.new("RGBA", img.size, (r, g, b, 255))
            coloured.putalpha(img.split()[3])
            img = coloured
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


class Sidebar(tk.Frame):
    def __init__(self, parent, on_navigate, **kwargs):
        super().__init__(parent, bg=_BG, width=SIDEBAR_W, **kwargs)
        self.pack_propagate(False)
        self._on_nav  = on_navigate
        self._active  = "home"
        self._btns    = {}
        self._imgs    = []          # keep PhotoImage refs alive

        self._build_logo()
        self._build_nav()
        self._build_logout()
        self.set_active("home")

    # ── Logo ─────────────────────────────────────────────────────────
    def _build_logo(self):
        logo_path = _os.path.join(BASE_DIR, "pocki_logo.png")
        ph = _load(logo_path, 44, 44)
        if ph:
            self._imgs.append(ph)

        frm = tk.Frame(self, bg=_BG, pady=14, padx=14)
        frm.pack(fill="x")

        if ph:
            tk.Label(frm, image=ph, bg=_BG).pack(side="left")
        tk.Label(frm, text="PockiTrack", bg=_BG,
                 fg="#000000", font=font(14, "bold")).pack(side="left", padx=(8, 0))

    # ── Nav items ─────────────────────────────────────────────────────
    def _build_nav(self):
        self._nav_frame = tk.Frame(self, bg=_BG, padx=10)
        self._nav_frame.pack(fill="x", pady=(10, 0))

        for key, label, icon_file in NAV_ITEMS:
            icon_path = _os.path.join(ASSETS_DIR, icon_file)
            # load dark-tinted icon for inactive state
            ico_dark  = _load(icon_path, 22, 22, tint="#616161")
            # load white-tinted icon for active state
            ico_white = _load(icon_path, 22, 22, tint="#FFFFFF")
            if ico_dark:
                self._imgs.append(ico_dark)
            if ico_white:
                self._imgs.append(ico_white)

            btn = self._make_pill(self._nav_frame, key, label,
                                  ico_dark, ico_white)
            self._btns[key] = btn

    def _draw_pill(self, canvas, colour):
        canvas.delete("pill_bg")
        w = canvas.winfo_width() or int(canvas["width"])
        h = canvas.winfo_height() or int(canvas["height"])
        if w < 2 or h < 2:
            return
        scale = 4
        sw, sh = w * scale, h * scale
        r = (h // 2) * scale
        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        cr = int(colour.lstrip("#"), 16)
        rgb = ((cr >> 16) & 255, (cr >> 8) & 255, cr & 255)
        draw.rounded_rectangle([0, 0, sw - 1, sh - 1], radius=r, fill=rgb + (255,))
        img = img.resize((w, h), Image.LANCZOS)
        ph = ImageTk.PhotoImage(img)
        self._imgs.append(ph)
        canvas._ph = ph
        canvas.create_image(0, 0, anchor="nw", image=ph, tags="pill_bg")
        canvas.tag_lower("pill_bg")

    def _make_pill(self, parent, key, label, ico_dark, ico_white):
        # outer frame (cream bg, full width)
        outer = tk.Frame(parent, bg=_BG, cursor="hand2")
        outer.pack(fill="x", pady=4)

        # pill canvas — rounded highlight background
        pill = tk.Canvas(outer, bg=_BG, height=46,
                         bd=0, highlightthickness=0)
        pill.pack(fill="x")
        pill.bind("<Configure>",
                  lambda e, c=pill: self._draw_pill(c, c._pill_colour))
        pill._pill_colour = _BG

        inner = tk.Frame(pill, bg=_BG)
        inner.place(relx=0, rely=0.5, anchor="w", x=12)

        lbl_icon = tk.Label(inner, bg=_BG,
                            image=ico_dark if ico_dark else "",
                            text="" if ico_dark else label[0],
                            fg=_NAV_FG, font=font(11))
        lbl_icon.pack(side="left")

        lbl_text = tk.Label(inner, text=label, bg=_BG,
                            fg=_NAV_FG, font=font(11, "bold"))
        lbl_text.pack(side="left", padx=(10, 0))

        # store refs for set_active / hover
        outer._key       = key
        outer._pill      = pill
        outer._inner     = inner
        outer._lbl_icon  = lbl_icon
        outer._lbl_text  = lbl_text
        outer._ico_dark  = ico_dark
        outer._ico_white = ico_white

        def _click(e=None):
            self.set_active(key)
            self._on_nav(key)

        def _enter(e):
            if key != self._active:
                self._set_pill_style(outer, _NAV_HOVER, _NAV_FG, "dark")

        def _leave(e):
            if key != self._active:
                self._set_pill_style(outer, _BG, _NAV_FG, "dark")

        for w in (outer, pill, inner, lbl_icon, lbl_text):
            w.bind("<Button-1>", _click)
            w.bind("<Enter>",    _enter)
            w.bind("<Leave>",    _leave)

        return outer

    # ── Logout ────────────────────────────────────────────────────────
    def _build_logout(self):
        logout_path = _os.path.join(ASSETS_DIR, "logout_icon.png")
        ico = _load(logout_path, 20, 20, tint="#616161")
        if ico:
            self._imgs.append(ico)

        bottom = tk.Frame(self, bg=_BG, padx=14, pady=20)
        bottom.pack(side="bottom", fill="x")

        btn = tk.Frame(bottom, bg=_LOGOUT_BG, height=45,
                       cursor="hand2",
                       highlightbackground="#E0D4C0",
                       highlightthickness=1)
        btn.pack(fill="x")
        btn.pack_propagate(False)

        inner = tk.Frame(btn, bg=_LOGOUT_BG)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        if ico:
            tk.Label(inner, image=ico, bg=_LOGOUT_BG).pack(side="left")
        tk.Label(inner, text="Log out", bg=_LOGOUT_BG,
                 fg=_LOGOUT_FG, font=font(10, "bold")).pack(side="left", padx=(8, 0))

        def _logout_click(e=None):
            self._on_nav("logout")

        def _logout_enter(e):
            btn.config(bg="#A24A00", highlightbackground="#A24A00")
            inner.config(bg="#A24A00")
            for w in inner.winfo_children():
                w.config(bg="#A24A00", fg="white")

        def _logout_leave(e):
            btn.config(bg=_LOGOUT_BG, highlightbackground="#E0D4C0")
            inner.config(bg=_LOGOUT_BG)
            for w in inner.winfo_children():
                w.config(bg=_LOGOUT_BG, fg=_LOGOUT_FG)

        for w in (btn, inner) + tuple(inner.winfo_children()):
            w.bind("<Button-1>", _logout_click)
            w.bind("<Enter>",    _logout_enter)
            w.bind("<Leave>",    _logout_leave)

    # ── helpers ───────────────────────────────────────────────────────
    def _set_pill_style(self, btn, bg, fg, icon_state):
        ico = btn._ico_white if icon_state == "white" else btn._ico_dark
        btn.config(bg=bg)
        btn._pill._pill_colour = bg
        self._draw_pill(btn._pill, bg)
        btn._inner.config(bg=bg)
        btn._lbl_icon.config(bg=bg, fg=fg,
                             image=ico if ico else "",
                             text="" if ico else btn._key[0])
        btn._lbl_text.config(bg=bg, fg=fg)

    def set_active(self, key):
        # deactivate old
        if self._active in self._btns:
            self._set_pill_style(self._btns[self._active], _BG, _NAV_FG, "dark")

        self._active = key

        # activate new
        if key in self._btns:
            self._set_pill_style(self._btns[key], _NAV_ACTIVE, "#FFFFFF", "white")
