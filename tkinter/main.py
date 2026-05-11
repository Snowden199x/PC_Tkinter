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
from screens.forgotpass_screen import ForgotPassScreen


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
        self._org       = None

        # Outer container
        self._shell = tk.Frame(self, bg=BG_CREAM)
        self._shell.pack(fill="both", expand=True)

        # Sidebar placeholder (always packed first so content fills the rest)
        self._sidebar_slot = tk.Frame(self._shell, bg=BG_CREAM, width=0)
        self._sidebar_slot.pack(side="left", fill="y")
        self._sidebar_slot.pack_propagate(False)

        self._sidebar = None

        # Right side: top bar + content stacked vertically
        self._right = tk.Frame(self._shell, bg=BG_CREAM)
        self._right.pack(side="left", fill="both", expand=True)

        # Top bar (hidden until login)
        self._topbar_frame = tk.Frame(self._right, bg=BG_CREAM, height=0)
        self._topbar_frame.pack(side="top", fill="x")
        self._topbar_frame.pack_propagate(False)
        self._topbar = None

        self._content = tk.Frame(self._right, bg=BG_CREAM)
        self._content.pack(side="top", fill="both", expand=True)

        # Start on the start screen
        self._show("start")

    # ── Poppins font loader ───────────────────────────────────────────
    def _try_load_poppins(self):
        """Try to register Poppins from a fonts/ directory if present."""
        fonts_dir = os.path.join(BASE_DIR, "assets", "fonts")
        if not os.path.isdir(fonts_dir):
            return
        try:
            # Windows: Add font using GDI
            for f in os.listdir(fonts_dir):
                if f.lower().endswith(".ttf"):
                    font_path = os.path.join(fonts_dir, f)
                    try:
                        from ctypes import windll
                        windll.gdi32.AddFontResourceW(font_path)
                        windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
                    except Exception:
                        pass
        except Exception:
            pass
        except Exception as e:
            print(f"Font loading note: {e}")

    # ── Navigation ────────────────────────────────────────────────────
    def _show(self, screen_name):
        """Destroy current screen and show the requested one."""
        for w in self._content.winfo_children():
            w.destroy()
        self.update_idletasks()

        if screen_name == "start":
            self._hide_sidebar()
            StartScreen(self._content,
                        on_login=lambda: self._show("login")).pack(
                fill="both", expand=True)

        elif screen_name == "login":
            self._hide_sidebar()
            LoginScreen(self._content,
                        on_login_success=self._post_login,
                        on_back=lambda: self._show("start"),
                        on_forgot=lambda: self._show("forgot")).pack(
                fill="both", expand=True)

        elif screen_name == "forgot":
            self._hide_sidebar()
            ForgotPassScreen(self._content,
                             on_back=lambda: self._show("login")).pack(
                fill="both", expand=True)

        elif screen_name == "change_password":
            self._hide_sidebar()
            from screens.change_password_screen import ChangePasswordScreen
            ChangePasswordScreen(
                self._content,
            org=self._org,
            on_success=lambda: self._show("home")
        ).pack(fill="both", expand=True)
            
        elif screen_name == "home":
            self._show_sidebar("home")
            HomeScreen(self._content, org=self._org).pack(fill="both", expand=True)

        elif screen_name == "history":
            self._show_sidebar("history")
            HistoryScreen(self._content, org=self._org).pack(fill="both", expand=True)

        elif screen_name == "wallet":
            self._show_sidebar("wallet")
            query = getattr(self, "_search_query", "")
            self._search_query = ""  # clear after use
            WalletScreen(self._content, org=self._org, search_query=query).pack(fill="both", expand=True)

        elif screen_name == "profile":
            self._show_sidebar("profile")
            ProfileScreen(self._content, org=self._org).pack(fill="both", expand=True)

        elif screen_name == "logout":
            self._hide_sidebar()
            self._logged_in = False
            self._show("start")

        self._current = screen_name
        if self._sidebar and screen_name in (
                "home", "history", "wallet", "profile"):
            self._sidebar.set_active(screen_name)

    def _post_login(self, org):
        self._logged_in = True
        self._org = org
        try:
            from db import get_profile
            profile = get_profile(org.get("id"))
            self._org["org_short_name"] = profile.get("org_short_name") or ""
        except Exception:
            pass
        if org.get("must_change_password"):
            self._show("change_password")
        else:
            self._show("home")

    def _show_sidebar(self, screen_name=None):
        if self._sidebar is None:
            self._sidebar = Sidebar(self._sidebar_slot,
                                    on_navigate=self._show)
            self._sidebar.pack(fill="both", expand=True)
            self._sidebar_slot.config(width=SIDEBAR_W)
        # Only show topbar on home screen
        if screen_name == "home":
            self._show_topbar()
        else:
            self._hide_topbar()

    def _hide_sidebar(self):
        if self._sidebar:
            self._sidebar.pack_forget()
            self._sidebar.destroy()
            self._sidebar = None
            self._sidebar_slot.config(width=0)
        self._hide_topbar()

    # ── Top bar ───────────────────────────────────────────────────────
    def _show_topbar(self):
        if self._topbar is not None:
            old = self._topbar
            self._topbar = None
            old.destroy()
            self.update_idletasks()
        self._topbar_frame.config(height=52)
        self._topbar = self._build_topbar(self._topbar_frame)

    def _hide_topbar(self):
        if self._topbar:
            self._topbar.destroy()
            self._topbar = None
        self._topbar_frame.config(height=0)

    def _build_topbar(self, parent):
        from PIL import Image, ImageTk, ImageDraw
        import os as _os

        bar = tk.Frame(parent, bg=BG_CREAM)
        bar.pack(fill="both", expand=True, padx=12, pady=(6, 0))

        assets = _os.path.join(BASE_DIR, "assets", "images")
        _imgs  = []   # keep PhotoImage refs alive

        PILL_H  = 38
        RADIUS  = 19   # fully pill-shaped
        WHITE   = "#FFFFFF"
        BORDER  = "#ECDDC6"
        HOVER_F = "#FFF7EC"
        HOVER_B = "#E59E2C"

        def _make_pill_image(w, h, fill, border, radius):
            scale = 4
            sw, sh, r = w * scale, h * scale, radius * scale
            img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # border ring
            br = int(border.lstrip("#"), 16)
            draw.rounded_rectangle([0, 0, sw-1, sh-1], radius=r,
                                   fill=((br>>16)&255,(br>>8)&255,br&255,255))
            # fill inset by 1 real pixel
            s = scale
            fr = int(fill.lstrip("#"), 16)
            draw.rounded_rectangle([s, s, sw-1-s, sh-1-s],
                                   radius=max(r-s, 0),
                                   fill=((fr>>16)&255,(fr>>8)&255,fr&255,255))
            img = img.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            _imgs.append(ph)
            return ph

        # ─── Profile pill ────────────────────────────────────────────
        org_name = ""
        if self._org:
            org_name = (self._org.get("org_short_name") or 
                        self._org.get("org_name", ""))

        _measure = tk.Frame(bar, bg=WHITE)
        av_size  = 26
        _av_tmp  = tk.Canvas(_measure, width=av_size, height=av_size,
                             bg=WHITE, bd=0, highlightthickness=0)
        _av_tmp.pack(side="left", padx=(10, 0))
        _nm_tmp  = tk.Label(_measure, text=org_name, bg=WHITE,
                            font=("Poppins", 9, "bold"), padx=6)
        _nm_tmp.pack(side="left")
        _cr_tmp  = tk.Label(_measure, text="▼", bg=WHITE,
                            font=("Poppins", 7), padx=0)
        _cr_tmp.pack(side="left", padx=(0, 10))
        bar.update_idletasks()
        pill_w = _measure.winfo_reqwidth()
        _measure.destroy()

        pill_cv = tk.Canvas(bar, width=pill_w, height=PILL_H,
                            bg=BG_CREAM, bd=0, highlightthickness=0,
                            cursor="hand2")
        pill_cv.pack(side="right")

        def _redraw_pill(fill=WHITE, border=BORDER):
            w = pill_cv.winfo_width() or pill_w
            ph = _make_pill_image(w, PILL_H, fill, border, RADIUS)
            pill_cv.delete("pill_bg")
            pill_cv.create_image(0, 0, anchor="nw", image=ph, tags="pill_bg")
            pill_cv.tag_lower("pill_bg")

        # avatar canvas embedded in pill
        av_cv = tk.Canvas(pill_cv, width=av_size, height=av_size,
                          bg=WHITE, bd=0, highlightthickness=0)
        pill_cv.create_window(10, PILL_H//2, anchor="w", window=av_cv)

        def _draw_avatar():
            av_cv.delete("all")
            av_cv.create_oval(0, 0, av_size, av_size, fill="#ECDDC6", outline="")

            # Try to load profile photo from DB first
            photo_img = None
            try:
                if self._org and self._org.get("id"):
                    from db import get_profile
                    profile = get_profile(self._org["id"])
                    photo_url = profile.get("profile_photo_url", "")
                    if photo_url:
                        import urllib.request, io
                        with urllib.request.urlopen(photo_url, timeout=5) as resp:
                            data = resp.read()
                        img = Image.open(io.BytesIO(data)).resize(
                            (av_size, av_size), Image.LANCZOS).convert("RGBA")
                        bg   = Image.new("RGBA", (av_size, av_size), (255,255,255,255))
                        mask = Image.new("L",    (av_size, av_size), 0)
                        ImageDraw.Draw(mask).ellipse((0,0,av_size,av_size), fill=255)
                        bg.paste(img, mask=mask)
                        ph = ImageTk.PhotoImage(bg.convert("RGB"))
                        _imgs.append(ph)
                        av_cv._ph = ph
                        av_cv.create_image(av_size//2, av_size//2,
                                        image=ph, anchor="center")
                        photo_img = ph
            except Exception:
                pass

            # Fallback to default_avatar.png
            if photo_img is None:
                default = _os.path.join(assets, "default_avatar.png")
                if _os.path.exists(default):
                    try:
                        img = Image.open(default).resize(
                            (av_size, av_size), Image.LANCZOS).convert("RGBA")
                        bg   = Image.new("RGBA", (av_size, av_size), (255,255,255,255))
                        mask = Image.new("L",    (av_size, av_size), 0)
                        ImageDraw.Draw(mask).ellipse((0,0,av_size,av_size), fill=255)
                        bg.paste(img, mask=mask)
                        ph = ImageTk.PhotoImage(bg.convert("RGB"))
                        _imgs.append(ph)
                        av_cv._ph = ph
                        av_cv.create_image(av_size//2, av_size//2,
                                        image=ph, anchor="center")
                    except Exception:
                        pass

        _draw_avatar()

        name_lbl = tk.Label(pill_cv, text=org_name, bg=WHITE,
                            fg=TEXT_DARK, font=("Poppins", 9, "bold"))
        pill_cv.create_window(10 + av_size + 6, PILL_H//2,
                              anchor="w", window=name_lbl)

        caret_lbl = tk.Label(pill_cv, text="▼", bg=WHITE,
                             fg="#828282", font=("Poppins", 7))
        pill_cv.create_window(pill_w - 10, PILL_H//2,
                              anchor="e", window=caret_lbl)

        pill_cv.bind("<Configure>", lambda e: _redraw_pill())
        bar.after(50, _redraw_pill)   # draw after layout settles

        # ─── Search bar ──────────────────────────────────────────────
        SRCH_W = 220

        srch_cv = tk.Canvas(bar, width=SRCH_W, height=PILL_H,
                            bg=BG_CREAM, bd=0, highlightthickness=0)
        srch_cv.pack(side="right", padx=(0, 8))

        def _redraw_srch(fill=WHITE, border=BORDER):
            w = srch_cv.winfo_width() or SRCH_W
            ph = _make_pill_image(w, PILL_H, fill, border, RADIUS)
            srch_cv.delete("srch_bg")
            srch_cv.create_image(0, 0, anchor="nw", image=ph, tags="srch_bg")
            srch_cv.tag_lower("srch_bg")

        icon_lbl = tk.Label(srch_cv, text="🔍", bg=WHITE,
                            fg="#9A8070", font=("Poppins", 9))
        srch_cv.create_window(12, PILL_H//2, anchor="w", window=icon_lbl)

        search_entry = tk.Entry(srch_cv, font=("Poppins", 9),
                                bd=0, relief="flat", bg=WHITE,
                                fg="#616161", width=16,
                                insertbackground=TEXT_DARK)
        search_entry.insert(0, "Search wallets...")
        srch_cv.create_window(38, PILL_H//2, anchor="w", window=search_entry)

        def _focus_in(e):
            if search_entry.get() == "Search wallets...":
                search_entry.delete(0, "end")
                search_entry.config(fg=TEXT_DARK)
            _redraw_srch(WHITE, HOVER_B)
        def _focus_out(e):
            if not search_entry.get():
                search_entry.insert(0, "Search wallets...")
                search_entry.config(fg="#616161")
            _redraw_srch(WHITE, BORDER)
        search_entry.bind("<FocusIn>",  _focus_in)
        search_entry.bind("<FocusOut>", _focus_out)
        def _do_search(e=None):
            query = search_entry.get().strip()
            if query == "Search wallets...":
                query = ""
            self._search_query = query
            self._show("wallet")

        search_entry.bind("<Return>", _do_search)

        srch_cv.bind("<Configure>", lambda e: _redraw_srch())
        bar.after(50, _redraw_srch)

        # ─── Dropdown ────────────────────────────────────────────────
        drop = tk.Frame(self, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        drop._open = False

        for txt, action in [("Profile", lambda: self._show("profile")),
                             ("Logout",  lambda: self._show("logout"))]:
            item = tk.Label(drop, text=txt, bg=WHITE, fg=TEXT_DARK,
                            font=("Poppins", 9), padx=16, pady=8,
                            anchor="w", cursor="hand2")
            item.pack(fill="x")
            item.bind("<Enter>", lambda e, b=item: b.config(bg="#F5F1E8"))
            item.bind("<Leave>", lambda e, b=item: b.config(bg=WHITE))
            item.bind("<Button-1>", lambda e, a=action: (
                drop.place_forget(), setattr(drop, "_open", False), a()))

        def _toggle_drop(e=None):
            if drop._open:
                drop.place_forget()
                drop._open = False
            else:
                self.update_idletasks()
                px = pill_cv.winfo_rootx() - self.winfo_rootx()
                py = pill_cv.winfo_rooty() - self.winfo_rooty() + PILL_H + 2
                drop.place(x=px, y=py, width=max(pill_cv.winfo_width(), 160))
                drop.lift()
                drop._open = True

        for w in (pill_cv, av_cv, name_lbl, caret_lbl):
            w.bind("<Button-1>", _toggle_drop)
            w.bind("<Enter>",    lambda e: _redraw_pill(HOVER_F, HOVER_B))
            w.bind("<Leave>",    lambda e: _redraw_pill(WHITE,   BORDER))

        return bar


if __name__ == "__main__":
    app = PockiTrackApp()
    app.mainloop()
#1
