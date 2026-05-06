import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, filedialog
from constants import *
from PIL import Image, ImageTk, ImageDraw
from db import get_profile, get_officers

_ASSETS  = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "assets", "images")
_BTN_BROWN  = "#A24A00"
_BTN_HOV    = "#8B3A00"
_BORDER     = "#ECDDC6"
_TAB_ACTIVE = "#A24A00"
_GREEN      = "#2E7D32"
_GRAD1      = "#ECDDC6"
_GRAD2      = "#F5F1E8"


def _load(name, w, h, cache):
    path = _os.path.join(_ASSETS, name)
    if not _os.path.exists(path):
        return None
    try:
        ph = ImageTk.PhotoImage(Image.open(path).resize((w, h), Image.LANCZOS))
        cache.append(ph)
        return ph
    except Exception:
        return None


def _circle_img(img_path, size, cache):
    """Crop image to circle."""
    try:
        img = Image.open(img_path).resize((size, size), Image.LANCZOS).convert("RGBA")
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        ph = ImageTk.PhotoImage(img)
        cache.append(ph)
        return ph
    except Exception:
        return None


class ProfileScreen(tk.Frame):
    def __init__(self, parent, org=None, **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._org   = org or {}
        self._imgs  = []
        self._profile = {}
        self._officers = []
        self._active_tab = "organization"
        self._build()

    def _build(self):
        outer = tk.Frame(self, bg=BG_CREAM, padx=20, pady=16)
        outer.pack(fill="both", expand=True)

        # rounded white box (same as home/wallet/history)
        box_canvas = tk.Canvas(outer, bg=BG_CREAM, bd=0, highlightthickness=0)
        box_canvas.pack(fill="both", expand=True)

        self._box = tk.Frame(box_canvas, bg=BG_WHITE, padx=30, pady=24)
        box_win = box_canvas.create_window(0, 0, anchor="nw", window=self._box)

        def _draw_bg(event=None):
            w = box_canvas.winfo_width()
            h = box_canvas.winfo_height()
            if w < 2 or h < 2:
                return
            r = 20
            box_canvas.itemconfig(box_win, width=w - r*2, height=h - r*2)
            box_canvas.coords(box_win, r, r)
            scale = 4
            sw, sh = w * scale, h * scale
            cr = int(BG_CREAM.lstrip("#"), 16)
            bg_rgb = ((cr >> 16) & 255, (cr >> 8) & 255, cr & 255)
            img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            img_bg = Image.new("RGBA", (sw, sh), bg_rgb + (255,))
            ImageDraw.Draw(img).rounded_rectangle(
                [0, 0, sw-1, sh-1], radius=r*scale, fill=(255, 255, 255, 255))
            img_bg.paste(img, mask=img)
            img_bg = img_bg.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img_bg)
            box_canvas._bg_ph = ph
            box_canvas.delete("box_bg")
            box_canvas.create_image(0, 0, anchor="nw", image=ph, tags="box_bg")
            box_canvas.tag_lower("box_bg")

        box_canvas.bind("<Configure>", _draw_bg)

        # title
        tk.Label(self._box, text="Profile", bg=BG_WHITE, fg=TEXT_DARK,
                 font=("Georgia", 22, "italic")).pack(anchor="w", pady=(0, 12))

        # load data
        loading = tk.Label(self._box, text="Loading informations...",
                           bg=BG_WHITE, fg=TEXT_MUTED, font=font(10))
        loading.pack(pady=20)
        self.update()
        try:
            self._profile  = get_profile(self._org.get("id"))
            self._officers = get_officers(self._org.get("id"))
        except Exception:
            self._profile  = {}
            self._officers = []
        loading.destroy()

        self._render_overview()
        self._render_tabs()

    # ── Overview banner ───────────────────────────────────────────────
    def _render_overview(self):
        p = self._profile
        banner = tk.Frame(self._box, bg=_GRAD1, padx=20, pady=20)
        banner.pack(fill="x", pady=(0, 16))

        # avatar circle
        av_frame = tk.Frame(banner, bg=_GRAD1)
        av_frame.pack(side="left", padx=(0, 20))

        av_canvas = tk.Canvas(av_frame, width=100, height=100,
                              bg=_GRAD1, bd=0, highlightthickness=0)
        av_canvas.pack()
        self._av_canvas = av_canvas
        self._draw_avatar(p.get("profile_photo_url", ""))

        cam_ico = _load("camera_icon.png", 16, 16, self._imgs)
        change_btn = tk.Label(av_frame,
                              text="  Change Photo" if not cam_ico else "",
                              image=cam_ico if cam_ico else "",
                              compound="left",
                              bg=_BORDER, fg=TEXT_DARK,
                              font=font(8), padx=10, pady=5, cursor="hand2")
        change_btn.pack(pady=(6, 0))
        change_btn.bind("<Button-1>", lambda e: self._change_photo())
        change_btn.bind("<Enter>", lambda e: change_btn.config(bg="#E59E2C", fg="white"))
        change_btn.bind("<Leave>", lambda e: change_btn.config(bg=_BORDER, fg=TEXT_DARK))

        # info
        info = tk.Frame(banner, bg=_GRAD1)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=p.get("org_name", ""), bg=_GRAD1, fg=TEXT_DARK,
                 font=font(16, "bold"), anchor="w").pack(anchor="w")
        tk.Label(info, text=p.get("org_short_name", ""), bg=_GRAD1, fg=_BTN_BROWN,
                 font=font(12), anchor="w").pack(anchor="w")
        tk.Label(info, text=p.get("department", ""), bg=_GRAD1, fg="#616161",
                 font=font(9), anchor="w").pack(anchor="w")
        tk.Label(info, text=p.get("school", ""), bg=_GRAD1, fg="#616161",
                 font=font(9), anchor="w").pack(anchor="w")
        if p.get("email"):
            tk.Label(info, text=p.get("email", ""), bg=_GRAD1, fg="#616161",
                     font=font(9), anchor="w").pack(anchor="w")

        # accreditation badge
        status = p.get("status", "Active")
        badge_bg = "#4CAF50" if status == "Active" else "#FF9800"
        badge = tk.Label(info, text=f"✓  {status}", bg=badge_bg, fg="white",
                         font=font(9, "bold"), padx=14, pady=6)
        badge.pack(anchor="w", pady=(10, 0))

    def _draw_avatar(self, url=""):
        self._av_canvas.delete("all")
        # draw circle background
        self._av_canvas.create_oval(0, 0, 100, 100, fill="#fff", outline="")
        # try loading photo
        if url and _os.path.exists(url):
            ph = _circle_img(url, 100, self._imgs)
            if ph:
                self._av_canvas.create_image(50, 50, image=ph, anchor="center")
                return
        # fallback default avatar
        default = _os.path.join(_ASSETS, "default_avatar.png")
        if _os.path.exists(default):
            ph = _circle_img(default, 96, self._imgs)
            if ph:
                self._av_canvas.create_image(50, 50, image=ph, anchor="center")
        else:
            self._av_canvas.create_text(50, 50, text="👤", font=font(28), fill=TEXT_MUTED)

    def _change_photo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path:
            ph = _circle_img(path, 100, self._imgs)
            if ph:
                self._av_canvas.delete("all")
                self._av_canvas.create_oval(0, 0, 100, 100, fill="#fff", outline="")
                self._av_canvas.create_image(50, 50, image=ph, anchor="center")

    # ── Tabs ──────────────────────────────────────────────────────────
    def _render_tabs(self):
        # tab nav bar
        nav = tk.Frame(self._box, bg=BG_WHITE)
        nav.pack(fill="x")
        tk.Frame(self._box, bg=_BORDER, height=2).pack(fill="x")

        self._tab_btns = {}
        self._tab_content = tk.Frame(self._box, bg=BG_WHITE)
        self._tab_content.pack(fill="both", expand=True, pady=(16, 0))

        for key, label in [("organization", "Organization Information"),
                            ("officers",     "Officers"),
                            ("accreditation","Accreditation Details")]:
            btn = tk.Label(nav, text=label, bg=BG_WHITE, fg="#616161",
                           font=font(10), padx=18, pady=10, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn

        self._switch_tab("organization")

    def _switch_tab(self, key):
        self._active_tab = key
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.config(fg=_TAB_ACTIVE, font=font(10, "bold"))
            else:
                btn.config(fg="#616161", font=font(10))
        for w in self._tab_content.winfo_children():
            w.destroy()
        if key == "organization":
            self._tab_org()
        elif key == "officers":
            self._tab_officers()
        elif key == "accreditation":
            self._tab_accreditation()

    # ── Organization tab ──────────────────────────────────────────────
    def _tab_org(self):
        p = self._profile
        card = tk.Frame(self._tab_content, bg=BG_WHITE,
                        highlightbackground=_BORDER, highlightthickness=2,
                        padx=24, pady=20)
        card.pack(fill="both", expand=True)

        self._org_entries = {}

        def _field(parent, label, value, full=False, editable=False):
            frm = tk.Frame(parent, bg=BG_WHITE)
            tk.Label(frm, text=label, bg=BG_WHITE, fg="#616161",
                     font=font(8), anchor="w").pack(anchor="w")
            entry = tk.Entry(frm, font=font(10), bd=1, relief="solid",
                             bg="#F9F9F9", fg=TEXT_DARK,
                             highlightbackground=_BORDER, highlightthickness=1,
                             state="readonly" if not editable else "normal")
            entry.insert(0, value)
            entry.pack(fill="x", ipady=6, pady=(4, 0))
            return frm, entry

        # row 1: org name full width
        r1 = tk.Frame(card, bg=BG_WHITE)
        r1.pack(fill="x", pady=(0, 12))
        frm, e = _field(r1, "Organization Name", p.get("org_name", ""))
        frm.pack(fill="x")
        self._org_entries["org_name"] = e

        # row 2: short name + department
        r2 = tk.Frame(card, bg=BG_WHITE)
        r2.pack(fill="x", pady=(0, 12))
        r2.columnconfigure(0, weight=1)
        r2.columnconfigure(1, weight=1)
        frm1, e1 = _field(r2, "Organization Shortened Name", p.get("org_short_name", ""))
        frm1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frm2, e2 = _field(r2, "Department", p.get("department", ""))
        frm2.grid(row=0, column=1, sticky="nsew")
        self._org_entries["org_short_name"] = e1
        self._org_entries["department"] = e2

        # row 3: school full width
        r3 = tk.Frame(card, bg=BG_WHITE)
        r3.pack(fill="x", pady=(0, 12))
        frm, e = _field(r3, "School / University", p.get("school", ""))
        frm.pack(fill="x")
        self._org_entries["school"] = e

        # row 4: email full width
        r4 = tk.Frame(card, bg=BG_WHITE)
        r4.pack(fill="x", pady=(0, 12))
        frm, e = _field(r4, "Email Address", p.get("email", ""))
        frm.pack(fill="x")
        self._org_entries["email"] = e

        # action buttons
        btn_row = tk.Frame(card, bg=BG_WHITE)
        btn_row.pack(anchor="e", pady=(8, 0))

        self._edit_btn = tk.Label(btn_row, text="Edit", bg=_BTN_BROWN, fg="white",
                                  font=font(9, "bold"), padx=24, pady=8, cursor="hand2")
        self._edit_btn.pack(side="left", padx=(0, 8))
        self._edit_btn.bind("<Button-1>", lambda e: self._enable_edit())
        self._edit_btn.bind("<Enter>", lambda e: self._edit_btn.config(bg=_BTN_HOV))
        self._edit_btn.bind("<Leave>", lambda e: self._edit_btn.config(bg=_BTN_BROWN))

        self._save_btn = tk.Label(btn_row, text="Save Changes", bg=_GREEN, fg="white",
                                  font=font(9, "bold"), padx=24, pady=8, cursor="hand2")
        self._save_btn.bind("<Enter>", lambda e: self._save_btn.config(bg="#1B5E20"))
        self._save_btn.bind("<Leave>", lambda e: self._save_btn.config(bg=_GREEN))

        self._cancel_btn = tk.Label(btn_row, text="Cancel", bg="#E0E0E0", fg="#616161",
                                    font=font(9, "bold"), padx=24, pady=8, cursor="hand2")
        self._cancel_btn.bind("<Button-1>", lambda e: self._cancel_edit())
        self._cancel_btn.bind("<Enter>", lambda e: self._cancel_btn.config(bg="#BDBDBD"))
        self._cancel_btn.bind("<Leave>", lambda e: self._cancel_btn.config(bg="#E0E0E0"))

    def _enable_edit(self):
        for key in ("org_short_name", "email"):
            e = self._org_entries.get(key)
            if e:
                e.config(state="normal", bg="white")
        self._edit_btn.pack_forget()
        self._save_btn.pack(side="left", padx=(0, 8))
        self._cancel_btn.pack(side="left")

    def _cancel_edit(self):
        p = self._profile
        for key in ("org_short_name", "email"):
            e = self._org_entries.get(key)
            if e:
                e.config(state="normal")
                e.delete(0, "end")
                e.insert(0, p.get(key, ""))
                e.config(state="readonly", bg="#F9F9F9")
        self._save_btn.pack_forget()
        self._cancel_btn.pack_forget()
        self._edit_btn.pack(side="left")

    # ── Officers tab ──────────────────────────────────────────────────
    def _tab_officers(self):
        p = self._tab_content

        hdr = tk.Frame(p, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 12))
        tk.Label(hdr, text="Organization Officers", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(12, "bold")).pack(side="left")

        # table header
        cols = ["Name", "Position", "Term Start", "Term End", "Status"]
        col_w = [180, 140, 110, 110, 80]
        thead = tk.Frame(p, bg=_BORDER)
        thead.pack(fill="x")
        for i, (col, w) in enumerate(zip(cols, col_w)):
            tk.Label(thead, text=col, bg=_BORDER, fg=TEXT_DARK,
                     font=font(9, "bold"), width=w//7, anchor="w",
                     padx=10, pady=8).pack(side="left")

        # scrollable rows
        canvas = tk.Canvas(p, bg=BG_WHITE, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(p, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_WHITE)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        if not self._officers:
            tk.Label(inner, text="No officers found.", bg=BG_WHITE,
                     fg=TEXT_MUTED, font=font(9)).pack(pady=20)
            return

        for o in self._officers:
            row = tk.Frame(inner, bg=BG_WHITE,
                           highlightbackground="#f0f0f0", highlightthickness=1)
            row.pack(fill="x")
            row.bind("<Enter>", lambda e, r=row: r.config(bg="#F9F9F9"))
            row.bind("<Leave>", lambda e, r=row: r.config(bg=BG_WHITE))

            for val, w in zip([
                o.get("name", ""),
                o.get("position", ""),
                (o.get("term_start") or "")[:10],
                (o.get("term_end") or "")[:10],
                o.get("status", ""),
            ], col_w):
                lbl = tk.Label(row, text=val, bg=BG_WHITE, fg=TEXT_DARK,
                               font=font(9), width=w//7, anchor="w",
                               padx=10, pady=10)
                lbl.pack(side="left")
                lbl.bind("<Enter>", lambda e, r=row: r.config(bg="#F9F9F9"))
                lbl.bind("<Leave>", lambda e, r=row: r.config(bg=BG_WHITE))

    # ── Accreditation tab ─────────────────────────────────────────────
    def _tab_accreditation(self):
        p = self._profile
        card = tk.Frame(self._tab_content, bg=BG_WHITE,
                        highlightbackground=_BORDER, highlightthickness=2,
                        padx=24, pady=20)
        card.pack(fill="x")

        tk.Label(card, text="Accreditation Information", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(12, "bold")).pack(anchor="w", pady=(0, 16))

        for label, value in [
            ("Date of Accreditation:", p.get("accreditation_date", "")),
            ("Current Status:",        p.get("status", "")),
        ]:
            row = tk.Frame(card, bg=BG_WHITE)
            row.pack(fill="x", pady=6)
            tk.Frame(card, bg="#f0f0f0", height=1).pack(fill="x")
            tk.Label(row, text=label, bg=BG_WHITE, fg="#616161",
                     font=font(9, "bold"), width=22, anchor="w").pack(side="left")
            color = _GREEN if "Active" in value else TEXT_DARK
            tk.Label(row, text=value, bg=BG_WHITE, fg=color,
                     font=font(9, "bold"), anchor="w").pack(side="left")
