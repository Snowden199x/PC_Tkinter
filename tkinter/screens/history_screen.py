import tkinter as tk
from tkinter import ttk
from constants import *
from datetime import datetime
from db import get_history_data

_MONTH_BG      = "#F3D58D"
_MONTH_NAV_BG  = "#ECDDC6"
_MONTH_NAV_HOV = "#E59E2C"
_FILTER_BORDER = "#ECDDC6"
_FILTER_ACTIVE = "#E59E2C"
_FILTER_HOV    = "#ECDDC6"
_INCOME_CLR    = "#2E7D32"
_EXPENSE_CLR   = "#C62828"

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]


class HistoryScreen(tk.Frame):
    def __init__(self, parent, org=None, **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._org   = org or {}
        now         = datetime.now()
        self._year  = now.year
        self._month = now.month
        self._filter = "all"
        self._build()

    def _make_pill_btn(self, parent, text, bg_hex, hover_hex,
                       fg="white", width=None, height=36,
                       font_spec=None, side=None, padx=0, pady=0,
                       command=None):
        """PIL-drawn fully-rounded pill button — same technique as wallet screen."""
        from PIL import Image, ImageDraw as _ID, ImageTk as _ITk
        fnt = font_spec or font(9, "bold")
        cv = tk.Canvas(parent, bd=0, highlightthickness=0,
                       bg=parent.cget("bg"), cursor="hand2",
                       height=height)
        if width:
            cv.config(width=width)
        if side is not None:
            cv.pack(side=side, padx=padx, pady=pady)
        else:
            cv.pack(padx=padx, pady=pady)

        def _draw(hover=False):
            cv.delete("all")
            bw = cv.winfo_width() or (width or 80)
            bh = cv.winfo_height() or height
            if bw < 4 or bh < 4:
                return
            active_bg = getattr(cv, "_active_bg", None)
            active_fg = getattr(cv, "_active_fg", None)
            is_active = active_bg is not None
            colour    = active_bg if is_active else (hover_hex if hover else bg_hex)
            txt_colour = active_fg if is_active else fg
            # support dynamic text (e.g. month label updates)
            label = getattr(cv, "_label_text", text)
            scale = 4
            sw, sh = bw * scale, bh * scale
            r = sh // 2          # fully rounded pill
            img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            cr = int(colour.lstrip("#"), 16)
            rgb = ((cr >> 16) & 255, (cr >> 8) & 255, cr & 255)
            if not is_active and not hover:
                bdr_hex = _FILTER_BORDER.lstrip("#")
                bdr_rgb = (int(bdr_hex[0:2], 16), int(bdr_hex[2:4], 16), int(bdr_hex[4:6], 16))
                _ID.Draw(img).rounded_rectangle(
                    [0, 0, sw - 1, sh - 1], radius=r,
                    fill=rgb + (255,),
                    outline=bdr_rgb + (255,), width=6)
            else:
                _ID.Draw(img).rounded_rectangle(
                    [0, 0, sw - 1, sh - 1], radius=r,
                    fill=rgb + (255,))
            img = img.resize((bw, bh), Image.LANCZOS)
            ph = _ITk.PhotoImage(img)
            cv._ph = ph
            cv.create_image(0, 0, anchor="nw", image=ph)
            cv.create_text(bw // 2, bh // 2, text=label,
                           fill=txt_colour, font=fnt, anchor="center")

        cv._redraw = _draw
        cv.bind("<Configure>", lambda e: _draw())
        cv.bind("<Enter>",     lambda e: _draw(hover=True))
        cv.bind("<Leave>",     lambda e: _draw(hover=False))
        if command:
            cv.bind("<Button-1>", lambda e: command())
        return cv

    def _build(self):
        from PIL import Image, ImageDraw
        outer = tk.Frame(self, bg=BG_CREAM, padx=12, pady=16)
        outer.pack(fill="both", expand=True)

        box_canvas = tk.Canvas(outer, bg=BG_CREAM, bd=0, highlightthickness=0)
        box_canvas.pack(fill="both", expand=True)

        self._box = tk.Frame(box_canvas, bg=BG_WHITE, padx=30, pady=24)
        box_win = box_canvas.create_window(0, 0, anchor="nw", window=self._box)

        def _draw_box_bg(event=None):
            w = box_canvas.winfo_width()
            h = box_canvas.winfo_height()
            if w < 2 or h < 2:
                return
            r = 20
            box_canvas.itemconfig(box_win, width=w - r * 2, height=h - r * 2)
            box_canvas.coords(box_win, r, r)
            scale = 4
            sw, sh = w * scale, h * scale
            cr = int(BG_CREAM.lstrip("#"), 16)
            bg_rgb = ((cr >> 16) & 255, (cr >> 8) & 255, cr & 255)
            img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            img_bg = Image.new("RGBA", (sw, sh), bg_rgb + (255,))
            ImageDraw.Draw(img).rounded_rectangle(
                [0, 0, sw - 1, sh - 1], radius=r * scale,
                fill=(255, 255, 255, 255))
            img_bg.paste(img, mask=img)
            img_bg = img_bg.resize((w, h), Image.LANCZOS)
            from PIL import ImageTk
            ph = ImageTk.PhotoImage(img_bg)
            box_canvas._bg_ph = ph
            box_canvas.delete("box_bg")
            box_canvas.create_image(0, 0, anchor="nw", image=ph, tags="box_bg")
            box_canvas.tag_lower("box_bg")

        box_canvas.bind("<Configure>", _draw_box_bg)

        # title
        tk.Label(self._box, text="Transaction History", bg=BG_WHITE,
                 fg=TEXT_DARK, font=("Playfair Display Italic", 22)).pack(anchor="w", pady=(0, 6))

        # month selector
        nav_row = tk.Frame(self._box, bg=BG_WHITE)
        nav_row.pack(pady=(10, 0))

        prev_cv = self._make_pill_btn(
            nav_row, "‹",
            bg_hex=_MONTH_NAV_BG, hover_hex=_MONTH_NAV_HOV,
            fg=TEXT_DARK, width=38, height=36,
            font_spec=font(16),
            side="left", padx=(0, 6),
            command=lambda: self._change_month(-1))

        # month label as a pill — stored so we can redraw with updated text
        self._month_cv = self._make_pill_btn(
            nav_row, self._month_str(),
            bg_hex=_MONTH_BG, hover_hex=_MONTH_BG,
            fg=TEXT_DARK, width=160, height=36,
            font_spec=font(11, "bold"),
            side="left", padx=0)

        nxt_cv = self._make_pill_btn(
            nav_row, "›",
            bg_hex=_MONTH_NAV_BG, hover_hex=_MONTH_NAV_HOV,
            fg=TEXT_DARK, width=38, height=36,
            font_spec=font(16),
            side="left", padx=(6, 0),
            command=lambda: self._change_month(+1))

        # filter tabs — pill-shaped, same rounding as wallet screen
        flt_row = tk.Frame(self._box, bg=BG_WHITE)
        flt_row.pack(pady=(18, 0))
        self._filter_btns = {}
        for key, label in [("all","All"), ("income","Income"), ("expense","Expense")]:
            cv = self._make_pill_btn(
                flt_row, label,
                bg_hex=BG_WHITE, hover_hex=_FILTER_HOV,
                fg=TEXT_DARK, width=80, height=34,
                font_spec=font(9),
                side="left", padx=5)
            cv.bind("<Button-1>", lambda e, k=key: self._set_filter(k))
            self._filter_btns[key] = cv
        self._update_filter_styles()

        # list area
        self._list_outer = tk.Frame(self._box, bg=BG_WHITE)
        self._list_outer.pack(fill="both", expand=True, pady=(10, 0))
        self._refresh()

    def _refresh(self):
        for w in self._list_outer.winfo_children():
            w.destroy()

        loading = tk.Label(self._list_outer, text="Loading...",
                           bg=BG_WHITE, fg=TEXT_MUTED, font=font(10))
        loading.pack(pady=20)
        self.update()

        try:
            rows = get_history_data(self._org.get("id"), self._year, self._month)
        except Exception:
            rows = []

        loading.destroy()

        if self._filter != "all":
            rows = [r for r in rows if r["kind"] == self._filter]

        canvas = tk.Canvas(self._list_outer, bg=BG_WHITE, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(self._list_outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_WHITE)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        # keep inner frame as wide as the canvas so cards stretch full width
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _scroll(e):
            try:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except Exception:
                pass
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _scroll))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Destroy>",
                    lambda e: canvas.unbind_all("<MouseWheel>") if e.widget is canvas else None)

        if not rows:
            frm = tk.Frame(inner, bg=BG_WHITE)
            frm.pack(expand=True, pady=40)
            tk.Label(frm, text="No transactions found.",
                     bg=BG_WHITE, fg=TEXT_DARK, font=font(11, "bold")).pack()
            tk.Label(frm, text="Try a different month or filter.",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(9)).pack(pady=(4, 0))
            return

        for t in rows:
            self._tx_card(inner, t)

    def _tx_card(self, parent, t):
        """Same card format as wallet screen _tx_item, with rounded border."""
        from PIL import Image, ImageDraw, ImageTk as _ITk
        date  = t.get("date_issued", "")[:10]
        desc  = t.get("description") or "—"
        qty   = t.get("quantity", 1)
        price = t.get("price", 0)
        total = qty * price
        kind  = t["kind"]
        amt   = total if kind == "income" else -total
        qty_line = f"{price:,.2f} x {qty} ({total:,.2f})"

        try:
            month_label = datetime.strptime(date, "%Y-%m-%d").strftime("%B").upper()
        except Exception:
            month_label = date

        if kind == "income":
            income_type = t.get("income_type") or "—"
            subtitle = f"{qty_line}  ·  {income_type}  ·  {desc}"
        else:
            particulars = t.get("particulars") or "—"
            subtitle = f"{qty_line}  ·  {particulars}  ·  {desc}"

        wallet_name = (t.get("wallet_name") or "").strip()
        color = _INCOME_CLR if amt >= 0 else _EXPENSE_CLR
        sign  = "+" if amt >= 0 else "-"

        RADIUS  = 8
        BDR_CLR = "#ECDDC6"
        HOV_CLR = "#E59E2C"
        B       = 2    # border thickness
        PAD     = RADIUS + B   # = 10 — keeps frame clear of corner arc pixels

        cv = tk.Canvas(parent, bg=BG_WHITE, bd=0, highlightthickness=0)
        cv.pack(fill="x", pady=2, padx=4)

        content = tk.Frame(cv, bg=BG_WHITE, padx=14, pady=10)
        content_win = cv.create_window(PAD, PAD, anchor="nw", window=content)

        def _draw(hover=False):
            bw = cv.winfo_width()
            ch = content.winfo_reqheight()
            if bw < 8 or ch < 4:
                return
            total_h = ch + PAD * 2
            cv.config(height=total_h)
            cv.itemconfig(content_win, width=bw - PAD * 2)

            bdr = HOV_CLR if hover else BDR_CLR
            scale = 4
            sw, sh = bw * scale, total_h * scale
            r = RADIUS * scale
            cr = int(bdr.lstrip("#"), 16)
            bdr_rgb = ((cr >> 16) & 255, (cr >> 8) & 255, cr & 255)
            img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            ImageDraw.Draw(img).rounded_rectangle(
                [B * scale, B * scale, sw - 1 - B * scale, sh - 1 - B * scale],
                radius=r,
                fill=(255, 255, 255, 255),
                outline=bdr_rgb + (255,), width=B * scale)
            img = img.resize((bw, total_h), Image.LANCZOS)
            bg_img = Image.new("RGB", (bw, total_h), (255, 255, 255))
            bg_img.paste(img, mask=img.split()[3])
            ph = _ITk.PhotoImage(bg_img)
            cv._ph = ph
            cv.delete("bg")
            cv.create_image(0, 0, anchor="nw", image=ph, tags="bg")
            cv.tag_lower("bg")

        # bind to size changes — use after() to let layout settle first
        content.bind("<Configure>", lambda e: cv.after(0, _draw))
        cv.bind("<Configure>",      lambda e: cv.after(0, _draw))
        for w in (cv, content):
            w.bind("<Enter>", lambda e: _draw(hover=True))
            w.bind("<Leave>", lambda e: _draw(hover=False))
        # initial draw after everything is packed
        cv.after(50, _draw)

        # ── card content ──────────────────────────────────────────────
        left = tk.Frame(content, bg=BG_WHITE)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(left, text=month_label, bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(9, "bold"), anchor="w").pack(anchor="w")
        tk.Label(left, text=subtitle, bg=BG_WHITE, fg=TEXT_MUTED,
                 font=font(8), anchor="w").pack(anchor="w")
        if wallet_name:
            tk.Label(left, text=wallet_name, bg=BG_WHITE, fg="#999999",
                     font=font(7), anchor="w").pack(anchor="w")
        tk.Label(left, text=date, bg=BG_WHITE, fg="#999999",
                 font=font(7), anchor="w").pack(anchor="w")

        tk.Label(content, text=f"{sign}₱{abs(amt):,.2f}",
                 bg=BG_WHITE, fg=color,
                 font=font(10, "bold")).pack(side="right", anchor="center")

    def _month_str(self):
        return f"{MONTHS[self._month - 1]} {self._year}"

    def _change_month(self, delta):
        self._month += delta
        if self._month > 12:
            self._month = 1
            self._year += 1
        elif self._month < 1:
            self._month = 12
            self._year -= 1
        # redraw the month pill with updated text
        if hasattr(self, "_month_cv"):
            self._month_cv._label_text = self._month_str()
            if hasattr(self._month_cv, "_redraw"):
                self._month_cv.after(0, self._month_cv._redraw)
        self._refresh()

    def _set_filter(self, key):
        self._filter = key
        self._update_filter_styles()
        self._refresh()

    def _update_filter_styles(self):
        for k, cv in self._filter_btns.items():
            if k == self._filter:
                cv._active_bg = _FILTER_ACTIVE
                cv._active_fg = "white"
            else:
                cv._active_bg = None
                cv._active_fg = None
            if hasattr(cv, "_redraw"):
                cv.after(0, cv._redraw)
