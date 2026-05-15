import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, filedialog
from constants import *
from PIL import Image, ImageTk, ImageDraw
from db import (get_profile, get_officers,
                update_profile, update_profile_photo,
                create_officer, update_officer, delete_officer)

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
    """Crop image to circle, composited onto white so no black corners."""
    try:
        raw = Image.open(img_path).resize((size, size), Image.LANCZOS).convert("RGBA")
        # white backing so transparent corners stay white, not black
        bg = Image.new("RGBA", (size, size), (255, 255, 255, 255))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        bg.paste(raw, mask=mask)
        ph = ImageTk.PhotoImage(bg.convert("RGB"))
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

    def _open_date_picker(self, entry_widget, parent_overlay):
        """Simple calendar date picker popup."""
        from datetime import datetime, date
        import calendar

        # parse current value or use today
        current = entry_widget.get().strip()
        try:
            sel = datetime.strptime(current, "%Y-%m-%d").date()
        except Exception:
            sel = date.today()

        state = {"year": sel.year, "month": sel.month, "selected": sel}

        # popup frame on top of overlay
        popup = tk.Frame(parent_overlay, bg=BG_WHITE, padx=0, pady=0,
                         highlightbackground="#E0D4C0", highlightthickness=2)
        popup.lift()

        def _position_popup(event=None):
            parent_overlay.update_idletasks()
            entry_widget.update_idletasks()
            # position below the entry widget
            ex = entry_widget.winfo_rootx() - parent_overlay.winfo_rootx()
            ey = entry_widget.winfo_rooty() - parent_overlay.winfo_rooty()
            eh = entry_widget.winfo_height()
            popup.place(x=ex, y=ey + eh + 4)

        def _build_calendar():
            for w in popup.winfo_children():
                w.destroy()

            y, m = state["year"], state["month"]
            month_name = calendar.month_name[m]

            # nav row
            nav = tk.Frame(popup, bg=BG_WHITE, padx=8, pady=6)
            nav.pack(fill="x")

            prev_btn = tk.Label(nav, text="‹", bg=BG_WHITE, fg=_BTN_BROWN,
                                font=font(14), cursor="hand2")
            prev_btn.pack(side="left")
            def _prev(e):
                if state["month"] == 1:
                    state["month"] = 12; state["year"] -= 1
                else:
                    state["month"] -= 1
                _build_calendar()
            prev_btn.bind("<Button-1>", _prev)

            tk.Label(nav, text=f"{month_name} {y}", bg=BG_WHITE, fg=TEXT_DARK,
                     font=font(10, "bold")).pack(side="left", expand=True)

            next_btn = tk.Label(nav, text="›", bg=BG_WHITE, fg=_BTN_BROWN,
                                font=font(14), cursor="hand2")
            next_btn.pack(side="right")
            def _next(e):
                if state["month"] == 12:
                    state["month"] = 1; state["year"] += 1
                else:
                    state["month"] += 1
                _build_calendar()
            next_btn.bind("<Button-1>", _next)

            tk.Frame(popup, bg=_BORDER, height=1).pack(fill="x")

            # day headers
            days_hdr = tk.Frame(popup, bg=BG_WHITE)
            days_hdr.pack(fill="x", padx=6, pady=(4, 0))
            for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
                tk.Label(days_hdr, text=d, bg=BG_WHITE, fg=TEXT_MUTED,
                         font=font(7, "bold"), width=3, anchor="center").pack(side="left")

            # calendar grid
            grid = tk.Frame(popup, bg=BG_WHITE, padx=6, pady=4)
            grid.pack()

            cal = calendar.monthcalendar(y, m)
            today = date.today()

            for week in cal:
                row_f = tk.Frame(grid, bg=BG_WHITE)
                row_f.pack()
                for day in week:
                    if day == 0:
                        tk.Label(row_f, text="", bg=BG_WHITE, width=3,
                                 font=font(8)).pack(side="left")
                    else:
                        d_obj = date(y, m, day)
                        is_sel = (d_obj == state["selected"])
                        is_today = (d_obj == today)

                        bg_c = _BTN_BROWN if is_sel else ("#FFF3E0" if is_today else BG_WHITE)
                        fg_c = "white" if is_sel else (_BTN_BROWN if is_today else TEXT_DARK)

                        day_lbl = tk.Label(row_f, text=str(day), bg=bg_c, fg=fg_c,
                                           font=font(8, "bold" if is_sel else "normal"),
                                           width=3, cursor="hand2", pady=2)
                        day_lbl.pack(side="left")

                        def _select(e, d=d_obj, lbl=day_lbl):
                            state["selected"] = d
                            entry_widget.config(state="normal")
                            entry_widget.delete(0, "end")
                            entry_widget.insert(0, d.strftime("%Y-%m-%d"))
                            entry_widget.config(state="normal")
                            popup.destroy()

                        day_lbl.bind("<Button-1>", _select)
                        day_lbl.bind("<Enter>", lambda e, l=day_lbl, s=is_sel:
                                     l.config(bg=_BTN_BROWN if s else "#ECDDC6"))
                        day_lbl.bind("<Leave>", lambda e, l=day_lbl, b=bg_c:
                                     l.config(bg=b))

            # close if click outside
            parent_overlay.bind("<Button-1>",
                lambda e: popup.destroy() if popup.winfo_exists() else None,
                add="+")

        _build_calendar()
        _position_popup()

    def _build(self):
        outer = tk.Frame(self, bg=BG_CREAM, padx=12, pady=16)
        outer.pack(fill="both", expand=True)

        # ── Scrollable wrapper ────────────────────────────────────────
        # The scroll canvas sits in outer; the white box lives INSIDE the
        # scrollable inner frame so it grows with its content and the whole
        # thing scrolls together.
        scroll_canvas = tk.Canvas(outer, bg=BG_CREAM, bd=0, highlightthickness=0)
        v_scroll = ttk.Scrollbar(outer, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        # inner frame — grows to fit all content, drives scrollregion
        scroll_inner = tk.Frame(scroll_canvas, bg=BG_CREAM)
        scroll_win = scroll_canvas.create_window((0, 0), window=scroll_inner, anchor="nw")

        def _on_inner_configure(event=None):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def _on_canvas_configure(event=None):
            # keep inner frame as wide as the canvas so content fills width
            scroll_canvas.itemconfig(scroll_win, width=scroll_canvas.winfo_width())

        scroll_inner.bind("<Configure>", _on_inner_configure)
        scroll_canvas.bind("<Configure>", _on_canvas_configure)

        # mouse-wheel scrolling
        def _on_mousewheel(event):
            scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ── White rounded box — content-sized, NOT viewport-sized ─────
        # We draw the rounded background on a canvas that is sized to match
        # self._box after every resize/content change.
        box_wrap = tk.Frame(scroll_inner, bg=BG_CREAM)
        box_wrap.pack(fill="x", expand=False, padx=0, pady=0)

        box_canvas = tk.Canvas(box_wrap, bg=BG_CREAM, bd=0, highlightthickness=0)
        box_canvas.pack(fill="x", expand=False)

        self._box = tk.Frame(box_canvas, bg=BG_WHITE, padx=30, pady=24)
        box_win = box_canvas.create_window(20, 20, anchor="nw", window=self._box)

        def _redraw_box(event=None):
            # Use the scroll canvas width so the white box fills the full width
            cw = scroll_canvas.winfo_width()
            if cw < 40:
                cw = self._box.winfo_reqwidth() + 40
            bh = self._box.winfo_reqheight()
            r  = 20
            ch = bh + r * 2
            box_canvas.config(width=cw, height=ch)
            box_canvas.itemconfig(box_win, width=cw - r * 2, height=bh)
            box_canvas.coords(box_win, r, r)

            # draw rounded-rect background
            scale = 4
            sw, sh = cw * scale, ch * scale
            cr = int(BG_CREAM.lstrip("#"), 16)
            bg_rgb = ((cr >> 16) & 255, (cr >> 8) & 255, cr & 255)
            img    = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            img_bg = Image.new("RGBA", (sw, sh), bg_rgb + (255,))
            ImageDraw.Draw(img).rounded_rectangle(
                [0, 0, sw - 1, sh - 1], radius=r * scale, fill=(255, 255, 255, 255))
            img_bg.paste(img, mask=img)
            img_bg = img_bg.resize((cw, ch), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img_bg)
            box_canvas._bg_ph = ph
            box_canvas.delete("box_bg")
            box_canvas.create_image(0, 0, anchor="nw", image=ph, tags="box_bg")
            box_canvas.tag_lower("box_bg")

        # redraw whenever the white box changes size (content added/removed)
        self._box.bind("<Configure>", _redraw_box)
        # also redraw when the scroll canvas width changes (window resize)
        scroll_canvas.bind("<Configure>",
                           lambda e: (_on_canvas_configure(), _redraw_box()))

        # title
        tk.Label(self._box, text="Profile", bg=BG_WHITE, fg=TEXT_DARK,
                 font=("Georgia", 22, "italic")).pack(anchor="w", pady=(0, 12))

        # loading card (matches web loading state)
        loading_card = tk.Frame(self._box, bg="#F5F5F5", padx=30, pady=30)
        loading_card.pack(pady=20)
        load_ico = _load("navi_profile.png", 48, 48, self._imgs)
        if load_ico:
            tk.Label(loading_card, image=load_ico, bg="#F5F5F5").pack()
        tk.Label(loading_card, text="Loading informations...", bg="#F5F5F5",
                 fg=TEXT_DARK, font=font(11, "bold")).pack(pady=(8, 2))
        tk.Label(loading_card, text="Please wait a moment.", bg="#F5F5F5",
                 fg=TEXT_MUTED, font=font(9)).pack()
        self.update()

        try:
            self._profile  = get_profile(self._org.get("id"))
            self._officers = get_officers(self._org.get("id"))
        except Exception:
            self._profile  = {}
            self._officers = []
        loading_card.destroy()

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

        # show default avatar immediately
        self._draw_avatar_default()

        # fetch the real photo in a background thread — UI never blocks
        photo_url = p.get("profile_photo_url", "")
        if photo_url:
            self._fetch_avatar_async(photo_url)

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
        self._ov_short = tk.Label(info, text=p.get("org_short_name", ""), bg=_GRAD1, fg=_BTN_BROWN,
                 font=font(12), anchor="w")
        self._ov_short.pack(anchor="w")
        tk.Label(info, text=p.get("department", ""), bg=_GRAD1, fg="#616161",
                 font=font(9), anchor="w").pack(anchor="w")
        tk.Label(info, text=p.get("school", ""), bg=_GRAD1, fg="#616161",
                 font=font(9), anchor="w").pack(anchor="w")
        if p.get("email"):
            self._ov_email = tk.Label(info, text=p.get("email", ""), bg=_GRAD1, fg="#616161",
                     font=font(9), anchor="w")
            self._ov_email.pack(anchor="w")

        # accreditation badge
        status = p.get("status", "Active")
        badge_bg = "#4CAF50" if status == "Active" else "#FF9800"
        badge = tk.Label(info, text=f"✓  {status}", bg=badge_bg, fg="white",
                         font=font(9, "bold"), padx=14, pady=6)
        badge.pack(anchor="w", pady=(10, 0))

    def _draw_avatar_default(self):
        """Draw the placeholder avatar immediately (no network needed)."""
        self._av_canvas.delete("all")
        self._av_canvas.create_oval(0, 0, 100, 100, fill="#fff", outline="")
        default = _os.path.join(_ASSETS, "default_avatar.png")
        if _os.path.exists(default):
            ph = _circle_img(default, 96, self._imgs)
            if ph:
                self._av_canvas.create_image(50, 50, image=ph, anchor="center")
                return
        self._av_canvas.create_text(50, 50, text="👤", font=font(28), fill=TEXT_MUTED)

    def _fetch_avatar_async(self, url):
        """Download the avatar in a background thread, then update the canvas on the main thread."""
        import threading
        from io import BytesIO

        def _worker():
            try:
                if url.startswith("http://") or url.startswith("https://"):
                    import urllib.request
                    req = urllib.request.Request(
                        url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = resp.read()
                    raw = Image.open(BytesIO(data))
                elif _os.path.exists(url):
                    raw = Image.open(url)
                else:
                    return  # nothing to load

                # crop to circle on white background (no black corners)
                raw = raw.resize((100, 100), Image.LANCZOS).convert("RGBA")
                bg  = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
                mask = Image.new("L", (100, 100), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, 100, 100), fill=255)
                bg.paste(raw, mask=mask)
                final = bg.convert("RGB")

                # hand the finished PIL image back to the main thread
                self.after(0, lambda img=final: self._apply_avatar_image(img))

            except Exception:
                pass  # keep showing the default avatar on any error

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_avatar_image(self, pil_img):
        """Called on the main thread to put the downloaded image onto the canvas."""
        try:
            ph = ImageTk.PhotoImage(pil_img)
            self._imgs.append(ph)          # keep reference so GC doesn't collect it
            self._av_canvas.delete("all")
            self._av_canvas.create_oval(0, 0, 100, 100, fill="#fff", outline="")
            self._av_canvas.create_image(50, 50, image=ph, anchor="center")
        except Exception:
            pass

    # kept for _change_photo local-file path
    def _draw_avatar(self, url=""):
        if url and (url.startswith("http://") or url.startswith("https://")):
            self._fetch_avatar_async(url)
        elif url and _os.path.exists(url):
            self._av_canvas.delete("all")
            self._av_canvas.create_oval(0, 0, 100, 100, fill="#fff", outline="")
            ph = _circle_img(url, 100, self._imgs)
            if ph:
                self._av_canvas.create_image(50, 50, image=ph, anchor="center")
        else:
            self._draw_avatar_default()

    def _change_photo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not path:
            return
        
        # show locally right away
        ph = _circle_img(path, 100, self._imgs)
        if ph:
            self._av_canvas.delete("all")
            self._av_canvas.create_oval(0, 0, 100, 100, fill="#fff", outline="")
            self._av_canvas.create_image(50, 50, image=ph, anchor="center")

        # upload to Supabase in background thread para hindi mag-freeze ang UI
        import threading

        def _upload():
            try:
                ext = path.rsplit(".", 1)[-1].lower()
                with open(path, "rb") as f:
                    image_bytes = f.read()
                public_url = update_profile_photo(self._org.get("id"), image_bytes, ext)
                if public_url:
                    self._profile["profile_photo_url"] = public_url
                    # redraw from public URL on main thread
                    self.after(0, lambda: self._draw_avatar(public_url))
            except Exception as ex:
                print(f"Photo upload failed: {ex}")

        threading.Thread(target=_upload, daemon=True).start()

    def _refresh_overview_labels(self):
        """Update the overview banner text labels after a profile save."""
        p = self._profile
        for attr, key in [
            ("_ov_short",  "org_short_name"),
            ("_ov_email",  "email"),
        ]:
            lbl = getattr(self, attr, None)
            if lbl:
                try:
                    lbl.config(text=p.get(key, ""))
                except Exception:
                    pass

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
                             highlightbackground=_BORDER, highlightthickness=1)
            # insert BEFORE setting readonly — readonly blocks insert()
            entry.insert(0, value or "")
            if not editable:
                entry.config(state="readonly")
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

        # inline error label (shown on save failure)
        self._save_err = tk.Label(card, text="", bg=BG_WHITE, fg="#C62828", font=font(8))
        self._save_err.pack(anchor="e", pady=(2, 0))

        self._edit_btn = tk.Label(btn_row, text="Edit", bg=_BTN_BROWN, fg="white",
                                  font=font(9, "bold"), padx=24, pady=8, cursor="hand2")
        self._edit_btn.pack(side="left", padx=(0, 8))
        self._edit_btn.bind("<Button-1>", lambda e: self._enable_edit())
        self._edit_btn.bind("<Enter>", lambda e: self._edit_btn.config(bg=_BTN_HOV))
        self._edit_btn.bind("<Leave>", lambda e: self._edit_btn.config(bg=_BTN_BROWN))

        self._save_btn = tk.Label(btn_row, text="Save Changes", bg=_GREEN, fg="white",
                                  font=font(9, "bold"), padx=24, pady=8, cursor="hand2")
        self._save_btn.bind("<Button-1>", lambda e: self._save_profile())
        self._save_btn.bind("<Enter>", lambda e: self._save_btn.config(bg="#1B5E20"))
        self._save_btn.bind("<Leave>", lambda e: self._save_btn.config(bg=_GREEN))

        self._cancel_btn = tk.Label(btn_row, text="Cancel", bg="#E0E0E0", fg="#616161",
                                    font=font(9, "bold"), padx=24, pady=8, cursor="hand2")
        self._cancel_btn.bind("<Button-1>", lambda e: self._cancel_edit())
        self._cancel_btn.bind("<Enter>", lambda e: self._cancel_btn.config(bg="#BDBDBD"))
        self._cancel_btn.bind("<Leave>", lambda e: self._cancel_btn.config(bg="#E0E0E0"))

    def _enable_edit(self):
        self._save_err.config(text="")
        for key in ("org_short_name", "email"):
            e = self._org_entries.get(key)
            if e:
                e.config(state="normal", bg="white")
        self._edit_btn.pack_forget()
        self._save_btn.pack(side="left", padx=(0, 8))
        self._cancel_btn.pack(side="left")

    def _cancel_edit(self):
        p = self._profile
        self._save_err.config(text="")
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

    def _save_profile(self):
        """Push org_short_name + email to Supabase, refresh local cache."""
        short = (self._org_entries.get("org_short_name") or tk.Entry()).get().strip()
        email = (self._org_entries.get("email")          or tk.Entry()).get().strip()

        if not short:
            self._save_err.config(text="Shortened name is required.")
            return
        if not email:
            self._save_err.config(text="Email is required.")
            return

        self._save_btn.config(text="Saving…", bg="#888888")
        self.update()
        try:
            update_profile(self._org.get("id"), org_short_name=short, email=email)
            # refresh local cache so overview + re-renders are accurate
            self._profile["org_short_name"] = short
            self._profile["email"]          = email
            self._save_err.config(text="")
            self._cancel_edit()          # lock fields, swap buttons back
            self._save_btn.config(text="Save Changes", bg=_GREEN)
            # refresh overview banner labels
            self._refresh_overview_labels()
        except Exception as ex:
            self._save_btn.config(text="Save Changes", bg=_GREEN)
            msg = str(ex)
            if "org_short_name" in msg or "shortened" in msg.lower():
                self._save_err.config(text="Shortened name already used by another org.")
            elif "email" in msg.lower():
                self._save_err.config(text="Email already used by another org.")
            else:
                self._save_err.config(text=f"Save failed: {msg[:60]}")

    # ── Officers tab ──────────────────────────────────────────────────
    # Column weights — proportional, not pixel-based, so header and rows
    # always share the exact same column geometry via grid columnconfigure.
    _OFF_COLS   = ["Name", "Position", "Term Start", "Term End", "Status", "Actions"]
    _OFF_WEIGHTS = [4, 3, 2, 2, 2, 2]   # relative widths

    def _tab_officers(self):
        p = self._tab_content

        hdr = tk.Frame(p, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 12))
        tk.Label(hdr, text="Organization Officers", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(12, "bold")).pack(side="left")

        # "+ Add Officer" button
        add_btn = tk.Label(hdr, text="+ Add Officer", bg=_BTN_BROWN, fg="white",
                           font=font(9, "bold"), padx=14, pady=6, cursor="hand2")
        add_btn.pack(side="right")
        add_btn.bind("<Button-1>", lambda e: self._open_officer_modal())
        add_btn.bind("<Enter>", lambda e: add_btn.config(bg=_BTN_HOV))
        add_btn.bind("<Leave>", lambda e: add_btn.config(bg=_BTN_BROWN))

        # ── Table container (header + rows share the same grid columns) ──
        table_frame = tk.Frame(p, bg=BG_WHITE)
        table_frame.pack(fill="x")
        for ci, w in enumerate(self._OFF_WEIGHTS):
            table_frame.columnconfigure(ci, weight=w, uniform="officers")

        # Header row
        for ci, col in enumerate(self._OFF_COLS):
            tk.Label(table_frame, text=col, bg=_BORDER, fg=TEXT_DARK,
                     font=font(9, "bold"), anchor="w",
                     padx=10, pady=8).grid(row=0, column=ci, sticky="nsew")

        # Separator
        tk.Frame(table_frame, bg="#D0D0D0", height=1).grid(
            row=1, column=0, columnspan=len(self._OFF_COLS), sticky="ew")

        # Scrollable body — canvas holds an inner frame that uses the same
        # columnconfigure so every data cell lines up with the header above.
        canvas = tk.Canvas(table_frame, bg=BG_WHITE, bd=0, highlightthickness=0)
        canvas.grid(row=2, column=0, columnspan=len(self._OFF_COLS), sticky="nsew")
        table_frame.rowconfigure(2, weight=1)

        sb = ttk.Scrollbar(p, orient="vertical", command=canvas.yview)
        sb.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=sb.set)

        inner = tk.Frame(canvas, bg=BG_WHITE)
        inner_win = canvas.create_window((0, 0), window=inner, anchor="nw")

        for ci, w in enumerate(self._OFF_WEIGHTS):
            inner.columnconfigure(ci, weight=w, uniform="officers")

        def _sync_inner_width(event=None):
            canvas.itemconfig(inner_win, width=canvas.winfo_width())
        canvas.bind("<Configure>", _sync_inner_width)
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        self._officers_inner = inner
        self._render_officer_rows(inner)

    def _render_officer_rows(self, inner, col_w=None):
        for w in inner.winfo_children():
            w.destroy()

        if not self._officers:
            # span all columns
            tk.Label(inner, text="No officers found.", bg=BG_WHITE,
                     fg=TEXT_MUTED, font=font(9)).grid(
                row=0, column=0, columnspan=len(self._OFF_COLS), pady=20, sticky="w", padx=10)
            return

        for idx, o in enumerate(self._officers):
            bg = BG_WHITE
            row_bg = tk.StringVar(value=bg)

            values = [
                o.get("name", ""),
                o.get("position", ""),
                (o.get("term_start") or "")[:10],
                (o.get("term_end")   or "")[:10],
                o.get("status", ""),
            ]

            cells = []
            for ci, val in enumerate(values):
                lbl = tk.Label(inner, text=val, bg=BG_WHITE, fg=TEXT_DARK,
                               font=font(9), anchor="w", padx=10, pady=10)
                lbl.grid(row=idx, column=ci, sticky="nsew")
                cells.append(lbl)

            # Actions cell
            act_frame = tk.Frame(inner, bg=BG_WHITE)
            act_frame.grid(row=idx, column=5, sticky="nsew", padx=6, pady=4)
            cells.append(act_frame)

            # hover highlight across the whole row
            def _enter(e, cs=cells):
                for c in cs:
                    c.config(bg="#F9F9F9")
            def _leave(e, cs=cells):
                for c in cs:
                    c.config(bg=BG_WHITE)
            for c in cells:
                c.bind("<Enter>", _enter)
                c.bind("<Leave>", _leave)

            # separator line
            tk.Frame(inner, bg="#F0F0F0", height=1).grid(
                row=idx, column=0, columnspan=len(self._OFF_COLS),
                sticky="sew")

            edit_lbl = tk.Label(act_frame, text="Edit", bg="#E3F2FD", fg="#1565C0",
                                font=font(8, "bold"), padx=8, pady=3, cursor="hand2")
            edit_lbl.pack(side="left", padx=(0, 4))
            edit_lbl.bind("<Button-1>", lambda e, i=idx: self._open_officer_modal(i))
            edit_lbl.bind("<Enter>", lambda e, l=edit_lbl: l.config(bg="#BBDEFB"))
            edit_lbl.bind("<Leave>", lambda e, l=edit_lbl: l.config(bg="#E3F2FD"))

            del_lbl = tk.Label(act_frame, text="Delete", bg="#FFEBEE", fg="#C62828",
                               font=font(8, "bold"), padx=8, pady=3, cursor="hand2")
            del_lbl.pack(side="left")
            del_lbl.bind("<Button-1>", lambda e, i=idx: self._confirm_delete_officer(i))
            del_lbl.bind("<Enter>", lambda e, l=del_lbl: l.config(bg="#FFCDD2"))
            del_lbl.bind("<Leave>", lambda e, l=del_lbl: l.config(bg="#FFEBEE"))

    # ── Officer Modal (Add / Edit) ─────────────────────────────────────
    def _open_officer_modal(self, edit_idx=None):
        """Full-screen overlay modal — same pattern as wallet add/edit dialog."""
        is_edit = edit_idx is not None
        o = self._officers[edit_idx] if is_edit else {}

        root = self.winfo_toplevel()
        root.update_idletasks()
        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        rw, rh = root.winfo_width(), root.winfo_height()

        # dimmed screenshot overlay
        try:
            from PIL import ImageGrab, ImageEnhance
            shot = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh))
            shot = ImageEnhance.Brightness(shot).enhance(0.5)
            _bg_ph = ImageTk.PhotoImage(shot)
        except Exception:
            _bg_ph = None

        overlay = tk.Frame(root, bg="black")
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        ov_cv = tk.Canvas(overlay, bd=0, highlightthickness=0)
        ov_cv.place(relx=0, rely=0, relwidth=1, relheight=1)
        if _bg_ph:
            ov_cv.create_image(0, 0, anchor="nw", image=_bg_ph)
            ov_cv._bg_ph = _bg_ph
        else:
            ov_cv.config(bg="black")
            ov_cv.create_rectangle(0, 0, rw, rh, fill="black",
                                   stipple="gray50", outline="")
        ov_cv.bind("<Button-1>", lambda e: overlay.destroy())

        # modal card — white, rounded feel via highlight border
        modal = tk.Frame(overlay, bg=BG_WHITE, padx=0, pady=0,
                         highlightbackground="#E0D4C0", highlightthickness=1)
        modal.place(relx=0.5, rely=0.5, anchor="center", width=460)
        modal.bind("<Button-1>", lambda e: "break")

        # ── modal header (border-bottom like CSS) ─────────────────────
        hdr = tk.Frame(modal, bg=BG_WHITE, padx=30, pady=20)
        hdr.pack(fill="x")
        title_text = "Edit Officer" if is_edit else "Add Officer"
        tk.Label(hdr, text=title_text, bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(13, "bold")).pack(side="left")
        close_lbl = tk.Label(hdr, text="×", bg=BG_WHITE, fg="#616161",
                             font=("Arial", 20), cursor="hand2",
                             width=2, height=1)
        close_lbl.pack(side="right")
        close_lbl.bind("<Button-1>", lambda e: overlay.destroy())
        close_lbl.bind("<Enter>", lambda e: close_lbl.config(bg="#F0F0F0"))
        close_lbl.bind("<Leave>", lambda e: close_lbl.config(bg=BG_WHITE))
        tk.Frame(modal, bg=_BORDER, height=2).pack(fill="x")

        # ── modal body ────────────────────────────────────────────────
        body = tk.Frame(modal, bg=BG_WHITE, padx=30, pady=20)
        body.pack(fill="x")

        err_labels = {}

        def _field(label_text, key):
            grp = tk.Frame(body, bg=BG_WHITE)
            grp.pack(fill="x", pady=(0, 10))
            tk.Label(grp, text=label_text, bg=BG_WHITE, fg=TEXT_DARK,
                     font=font(8, "bold")).pack(anchor="w")
            e = tk.Entry(grp, font=font(10), bd=1, relief="solid",
                         bg="#F9F9F9", fg=TEXT_DARK,
                         highlightbackground=_BORDER, highlightthickness=1)
            e.pack(fill="x", ipady=7, pady=(4, 0))
            err = tk.Label(grp, text="", bg=BG_WHITE, fg="#C62828", font=font(7))
            err.pack(anchor="w")
            err_labels[key] = err
            return e

        e_name     = _field("Name",     "name")
        e_position = _field("Position", "position")
        e_name.insert(0,     o.get("name", ""))
        e_position.insert(0, o.get("position", ""))

        # term start / end side by side
        term_row = tk.Frame(body, bg=BG_WHITE)
        term_row.pack(fill="x", pady=(0, 10))
        term_row.columnconfigure(0, weight=1)
        term_row.columnconfigure(1, weight=1)

        def _term_field(parent, col, label_text, key):
            grp = tk.Frame(parent, bg=BG_WHITE)
            grp.grid(row=0, column=col, sticky="nsew",
                     padx=(0, 8) if col == 0 else (8, 0))
            tk.Label(grp, text=label_text, bg=BG_WHITE, fg=TEXT_DARK,
                     font=font(8, "bold")).pack(anchor="w")
            e = tk.Entry(grp, font=font(10), bd=1, relief="solid",
                         bg="#F9F9F9", fg=TEXT_DARK,
                         highlightbackground=_BORDER, highlightthickness=1)
            e.pack(fill="x", ipady=7, pady=(4, 0))
            err = tk.Label(grp, text="", bg=BG_WHITE, fg="#C62828", font=font(7))
            err.pack(anchor="w")
            err_labels[key] = err
            return e

        e_start = _term_field(term_row, 0, "Term Start (YYYY-MM-DD)", "term_start")
        e_end   = _term_field(term_row, 1, "Term End (YYYY-MM-DD)",   "term_end")
        e_start.insert(0, (o.get("term_start") or "")[:10])
        e_end.insert(0,   (o.get("term_end")   or "")[:10])
        e_start.bind("<Button-1>", lambda e: self._open_date_picker(e_start, overlay))
        e_end.bind("<Button-1>",   lambda e: self._open_date_picker(e_end, overlay))

        # status dropdown
        grp_status = tk.Frame(body, bg=BG_WHITE)
        grp_status.pack(fill="x", pady=(0, 4))
        tk.Label(grp_status, text="Status", bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(8, "bold")).pack(anchor="w")
        status_var = tk.StringVar(value=o.get("status", "active"))
        status_cb = ttk.Combobox(grp_status, textvariable=status_var,
                                 values=["active", "inactive"],
                                 state="readonly", font=font(10))
        status_cb.pack(fill="x", ipady=4, pady=(4, 0))

        # ── modal footer (border-top like CSS) ────────────────────────
        tk.Frame(modal, bg=_BORDER, height=2).pack(fill="x")
        footer = tk.Frame(modal, bg=BG_WHITE, padx=30, pady=16)
        footer.pack(fill="x")

        cancel_btn = tk.Label(footer, text="Cancel", bg=BG_WHITE, fg="#616161",
                              font=font(9, "bold"), padx=20, pady=8,
                              cursor="hand2",
                              highlightbackground=_BORDER, highlightthickness=1)
        cancel_btn.pack(side="left")
        cancel_btn.bind("<Button-1>", lambda e: overlay.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(bg="#F5F1E8"))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(bg=BG_WHITE))

        def _show_err(key, msg):
            if key in err_labels:
                err_labels[key].config(text=msg)

        def _clear_err(key):
            if key in err_labels:
                err_labels[key].config(text="")

        def _save(e=None):
            name_val  = e_name.get().strip()
            pos_val   = e_position.get().strip()
            start_val = e_start.get().strip()
            end_val   = e_end.get().strip()
            stat_val  = status_var.get()

            valid = True
            for key, val, label in [
                ("name",       name_val,  "Name"),
                ("position",   pos_val,   "Position"),
                ("term_start", start_val, "Term Start"),
                ("term_end",   end_val,   "Term End"),
            ]:
                if not val:
                    _show_err(key, f"{label} is required.")
                    valid = False
                else:
                    _clear_err(key)

            if not valid:
                return

            save_btn.config(text="Saving…", bg="#888888")
            overlay.update()
            try:
                if is_edit:
                    officer_id = self._officers[edit_idx].get("id")
                    updated = update_officer(
                        officer_id=officer_id,
                        org_id=self._org.get("id"),
                        name=name_val, position=pos_val,
                        term_start=start_val, term_end=end_val,
                        status=stat_val,
                    )
                    self._officers[edit_idx].update(updated or {
                        "name": name_val, "position": pos_val,
                        "term_start": start_val, "term_end": end_val,
                        "status": stat_val,
                    })
                else:
                    new_officer = create_officer(
                        org_id=self._org.get("id"),
                        name=name_val, position=pos_val,
                        term_start=start_val, term_end=end_val,
                        status=stat_val,
                    )
                    self._officers.append(new_officer)
                overlay.destroy()
                if hasattr(self, "_officers_inner"):
                    self._render_officer_rows(self._officers_inner)
            except Exception as ex:
                save_btn.config(text="Save Officer", bg=_BTN_BROWN)
                _show_err("name", f"Save failed: {str(ex)[:60]}")

        save_btn = tk.Label(footer, text="Save Officer", bg=_BTN_BROWN, fg="white",
                            font=font(9, "bold"), padx=20, pady=8, cursor="hand2")
        save_btn.pack(side="right")
        save_btn.bind("<Button-1>", _save)
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg=_BTN_HOV))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg=_BTN_BROWN))

    # ── Delete Confirmation Modal ──────────────────────────────────────
    def _confirm_delete_officer(self, idx):
        """Full-screen overlay delete confirm — same pattern as wallet dialogs."""
        o = self._officers[idx]

        root = self.winfo_toplevel()
        root.update_idletasks()
        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        rw, rh = root.winfo_width(), root.winfo_height()

        try:
            from PIL import ImageGrab, ImageEnhance
            shot = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh))
            shot = ImageEnhance.Brightness(shot).enhance(0.5)
            _bg_ph = ImageTk.PhotoImage(shot)
        except Exception:
            _bg_ph = None

        overlay = tk.Frame(root, bg="black")
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        ov_cv = tk.Canvas(overlay, bd=0, highlightthickness=0)
        ov_cv.place(relx=0, rely=0, relwidth=1, relheight=1)
        if _bg_ph:
            ov_cv.create_image(0, 0, anchor="nw", image=_bg_ph)
            ov_cv._bg_ph = _bg_ph
        else:
            ov_cv.config(bg="black")
            ov_cv.create_rectangle(0, 0, rw, rh, fill="black",
                                   stipple="gray50", outline="")
        ov_cv.bind("<Button-1>", lambda e: overlay.destroy())

        modal = tk.Frame(overlay, bg=BG_WHITE, padx=0, pady=0,
                         highlightbackground="#E0D4C0", highlightthickness=1)
        modal.place(relx=0.5, rely=0.5, anchor="center", width=400)
        modal.bind("<Button-1>", lambda e: "break")

        # header
        hdr = tk.Frame(modal, bg=BG_WHITE, padx=30, pady=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Delete Officer", bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(13, "bold")).pack(side="left")
        close_lbl = tk.Label(hdr, text="×", bg=BG_WHITE, fg="#616161",
                             font=("Arial", 20), cursor="hand2",
                             width=2, height=1)
        close_lbl.pack(side="right")
        close_lbl.bind("<Button-1>", lambda e: overlay.destroy())
        close_lbl.bind("<Enter>", lambda e: close_lbl.config(bg="#F0F0F0"))
        close_lbl.bind("<Leave>", lambda e: close_lbl.config(bg=BG_WHITE))
        tk.Frame(modal, bg=_BORDER, height=2).pack(fill="x")

        # body
        body = tk.Frame(modal, bg=BG_WHITE, padx=30, pady=24)
        body.pack(fill="x")
        name = o.get("name", "this officer")
        tk.Label(body,
                 text=f'Are you sure you want to delete "{name}" from the officers list?',
                 bg=BG_WHITE, fg=TEXT_DARK, font=font(10),
                 wraplength=320, justify="left").pack(anchor="w")

        # footer
        tk.Frame(modal, bg=_BORDER, height=2).pack(fill="x")
        footer = tk.Frame(modal, bg=BG_WHITE, padx=30, pady=16)
        footer.pack(fill="x")

        cancel_btn = tk.Label(footer, text="Cancel", bg=BG_WHITE, fg="#616161",
                              font=font(9, "bold"), padx=20, pady=8,
                              cursor="hand2",
                              highlightbackground=_BORDER, highlightthickness=1)
        cancel_btn.pack(side="left")
        cancel_btn.bind("<Button-1>", lambda e: overlay.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(bg="#F5F1E8"))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(bg=BG_WHITE))

        def _do_delete(e=None):
            del_btn.config(text="Deleting…", bg="#888888")
            overlay.update()
            try:
                officer_id = o.get("id")
                if officer_id:
                    delete_officer(officer_id, self._org.get("id"))
                self._officers = [x for x in self._officers if x.get("id") != officer_id]
                overlay.destroy()
                if hasattr(self, "_officers_inner"):
                    self._render_officer_rows(self._officers_inner)
            except Exception as ex:
                del_btn.config(text="Delete", bg="#C62828")
                # show error in body
                tk.Label(body, text=f"Delete failed: {str(ex)[:60]}",
                         bg=BG_WHITE, fg="#C62828", font=font(8)).pack(anchor="w", pady=(6, 0))

        del_btn = tk.Label(footer, text="Delete", bg="#C62828", fg="white",
                           font=font(9, "bold"), padx=20, pady=8, cursor="hand2")
        del_btn.pack(side="right")
        del_btn.bind("<Button-1>", _do_delete)
        del_btn.bind("<Enter>", lambda e: del_btn.config(bg="#B71C1C"))
        del_btn.bind("<Leave>", lambda e: del_btn.config(bg="#C62828"))

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
