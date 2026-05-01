import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
from constants import *
from datetime import datetime
from db import get_home_data
from PIL import Image, ImageTk

WALLET_COLORS = ["#A25517", "#C4872A", "#4CAF79", "#9B6FCF", "#4AA8D8", "#E05C5C"]
_ASSETS = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "assets", "images")


def _load_img(name, w, h, cache):
    path = _os.path.join(_ASSETS, name)
    if not _os.path.exists(path):
        return None
    try:
        img = Image.open(path).resize((w, h), Image.LANCZOS)
        ph = ImageTk.PhotoImage(img)
        cache.append(ph)
        return ph
    except Exception:
        return None


class HomeScreen(tk.Frame):
    def __init__(self, parent, org=None, **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._org   = org or {}
        self._data  = {}
        self._imgs  = []
        self._build()

    # ── initial build with loading state ─────────────────────────────
    def _build(self):
        loading = tk.Label(self, text="Loading informations...",
                           bg=BG_CREAM, fg=TEXT_MUTED, font=font(11))
        loading.pack(expand=True)
        self.update()
        try:
            self._data = get_home_data(self._org.get("id"))
        except Exception:
            self._data = {"total_balance": 0, "total_wallets": 0,
                          "income_month": 0, "expense_month": 0,
                          "wallets": [], "transactions": [], "wallet_map": {}}
        loading.destroy()
        self._render()

    # ── main render ───────────────────────────────────────────────────
    def _render(self):
        d        = self._data
        org_name = self._org.get("org_name", "Organization")
        date_str = datetime.now().strftime("%A, %B %d, %Y")
        now      = datetime.now()
        month_lbl = now.strftime("%B")

        # ── white content box ────────────────────────────────────────────────────
        outer = tk.Frame(self, bg=BG_CREAM, padx=20, pady=16)
        outer.pack(fill="both", expand=True)

        box_canvas = tk.Canvas(outer, bg=BG_CREAM, bd=0, highlightthickness=0)
        box_canvas.pack(fill="both", expand=True)

        box = tk.Frame(box_canvas, bg=BG_WHITE, padx=30, pady=24)
        box_win = box_canvas.create_window(0, 0, anchor="nw", window=box)

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
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            cr = int(BG_CREAM.lstrip("#"), 16)
            bg_rgb = ((cr >> 16) & 255, (cr >> 8) & 255, cr & 255)
            img_bg = Image.new("RGBA", (sw, sh), bg_rgb + (255,))
            ImageDraw.Draw(img).rounded_rectangle(
                [0, 0, sw - 1, sh - 1], radius=r * scale,
                fill=(255, 255, 255, 255))
            img_bg.paste(img, mask=img)
            img_bg = img_bg.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img_bg)
            box_canvas._bg_ph = ph
            box_canvas.delete("box_bg")
            box_canvas.create_image(0, 0, anchor="nw", image=ph, tags="box_bg")
            box_canvas.tag_lower("box_bg")

        box_canvas.bind("<Configure>", _draw_box_bg)

        # ── Header ────────────────────────────────────────────────────
        hdr = tk.Frame(box, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 4))

        tk.Label(hdr,
                 text=f"Hello, {org_name}",
                 bg=BG_WHITE, fg=TEXT_DARK,
                 font=("Georgia", 22, "italic")).pack(anchor="w")
        tk.Label(hdr,
                 text=date_str,
                 bg=BG_WHITE, fg=TEXT_MUTED,
                 font=font(9)).pack(anchor="w")

        # ── Amber gradient summary banner ─────────────────────────────
        banner_canvas = tk.Canvas(box, bg=BG_WHITE, bd=0, highlightthickness=0, height=100)
        banner_canvas.pack(fill="x", pady=(14, 0))

        def _draw_banner(event=None):
            w = banner_canvas.winfo_width()
            h = banner_canvas.winfo_height()
            if w < 2 or h < 2:
                return
            scale = 4
            sw, sh, r = w * scale, h * scale, 25 * scale
            from PIL import Image, ImageDraw
            c1, c2, c3 = (0xF3, 0xD5, 0x8D), (0xEC, 0xB9, 0x5D), (0xE5, 0x9E, 0x2C)
            grad = Image.new("RGB", (sw, 1))
            for x in range(sw):
                t = x / (sw - 1)
                if t <= 0.54:
                    s = t / 0.54
                    px = tuple(int(c1[i] + (c2[i] - c1[i]) * s) for i in range(3))
                else:
                    s = (t - 0.54) / 0.46
                    px = tuple(int(c2[i] + (c3[i] - c2[i]) * s) for i in range(3))
                grad.putpixel((x, 0), px)
            grad = grad.resize((sw, sh), Image.NEAREST)
            mask = Image.new("L", (sw, sh), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw-1, sh-1], radius=r, fill=255)
            result = Image.new("RGBA", (sw, sh), (255, 255, 255, 0))
            result.paste(grad, mask=mask)
            result = result.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(result)
            banner_canvas._ph = ph
            banner_canvas.delete("banner_bg")
            banner_canvas.create_image(0, 0, anchor="nw", image=ph, tags="banner_bg")
            banner_canvas.tag_lower("banner_bg")

        banner_canvas.bind("<Configure>", _draw_banner)

        summary_items = [
            ("Total Balance",             f"₱{d['total_balance']:,.2f}"),
            (f"Income this {month_lbl}",  f"₱{d['income_month']:,.2f}"),
            (f"Expenses this {month_lbl}", f"₱{d['expense_month']:,.2f}"),
            ("Reports submitted",          str(d.get("reports", 0))),
        ]
        card_frames = []
        for i, (lbl, val) in enumerate(summary_items):
            card_cv = tk.Canvas(banner_canvas, bd=0, highlightthickness=0)
            lbl_widget = tk.Label(card_cv, text=lbl, fg="#5a3a00", font=font(8, "medium"))
            val_widget = tk.Label(card_cv, text=val, fg="#3a2000", font=font(12))
            card_frames.append((i, card_cv, lbl_widget, val_widget))

        def _draw_card(cv, lbl_w, val_w, grad_slice_x, grad_slice_w, card_w, card_h):
            from PIL import Image, ImageDraw, ImageFilter
            cv.delete("card_bg")
            if card_w < 4 or card_h < 4:
                return
            scale = 4
            sw, sh, r = card_w * scale, card_h * scale, 15 * scale
            c1, c2, c3 = (0xF3, 0xD5, 0x8D), (0xEC, 0xB9, 0x5D), (0xE5, 0x9E, 0x2C)
            t = (grad_slice_x + grad_slice_w / 2)
            if t <= 0.54:
                s = t / 0.54
                base = tuple(int(c1[i] + (c2[i] - c1[i]) * s) for i in range(3))
            else:
                s = (t - 0.54) / 0.46
                base = tuple(int(c2[i] + (c3[i] - c2[i]) * s) for i in range(3))
            blended = tuple(int(base[i] * 0.6 + 255 * 0.4) for i in range(3))
            mask = Image.new("L", (sw, sh), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw-1, sh-1], radius=r, fill=255)
            card_img = Image.new("RGBA", (sw, sh), blended + (255,))
            result = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            result.paste(card_img, mask=mask)
            result = result.resize((card_w, card_h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(result)
            cv._ph = ph
            cv.create_image(0, 0, anchor="nw", image=ph, tags="card_bg")
            cv.tag_lower("card_bg")
            hex_bg = "#{:02x}{:02x}{:02x}".format(*blended)
            cv.config(bg=hex_bg)          # ← fixes the white corner bleed
            lbl_w.config(bg=hex_bg)
            val_w.config(bg=hex_bg)
            lbl_w.place(x=14, y=10)
            val_w.place(x=14, y=30)

        def _place_cards(event=None):
            w = banner_canvas.winfo_width()
            h = banner_canvas.winfo_height()
            if w < 2 or h < 2:
                return
            n = len(card_frames)
            pad = 12
            card_w = (w - pad * (n + 1)) // n
            card_h = h - pad * 2
            for i, cv, lbl_w, val_w in card_frames:
                x = pad + i * (card_w + pad)
                cv.place(x=x, y=pad, width=card_w, height=card_h)
                t_center = (x + card_w / 2) / w
                _draw_card(cv, lbl_w, val_w, t_center, card_w / w, card_w, card_h)

        banner_canvas.bind("<Configure>", lambda e: (_draw_banner(e), _place_cards(e)))

        # ── Overview row ──────────────────────────────────────────────
        overview = tk.Frame(box, bg=BG_WHITE)
        overview.pack(fill="both", expand=True, pady=(20, 0))
        overview.columnconfigure(0, weight=1)
        overview.columnconfigure(1, weight=1)

        self._build_wallets(overview, d["wallets"])
        self._build_history(overview, d["transactions"])

    # ── Wallets panel ─────────────────────────────────────────────────
    def _build_wallets(self, parent, wallets):
        col = tk.Frame(parent, bg=BG_WHITE)
        col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(col, text="Wallets Overview", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(11, "medium")).pack(anchor="w", pady=(0, 8))

        scroll_outer = tk.Frame(col, bg=BG_WHITE,
                                highlightbackground=DIVIDER,
                                highlightthickness=1)
        scroll_outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_outer, bg=BG_WHITE,
                           bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(scroll_outer, orient="vertical",
                           command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_WHITE)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        wallet_img = _load_img("wallet.png", 55, 48, self._imgs)

        if not wallets:
            tk.Label(inner, text="No wallets found.",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(9)).pack(pady=20)
        else:
            for i, (name, balance) in enumerate(wallets):
                color = WALLET_COLORS[i % len(WALLET_COLORS)]
                self._wallet_card(inner, name, balance, color, wallet_img)

    def _wallet_card(self, parent, name, balance, color, wallet_img):
        card = tk.Frame(parent, bg=BG_WHITE,
                        highlightbackground="#F0E6D5",
                        highlightthickness=1,
                        padx=14, pady=12)
        card.pack(fill="x", pady=5, padx=4)

        icon_f = tk.Frame(card, bg=BG_WHITE)
        icon_f.pack(side="left", padx=(0, 12))
        if wallet_img:
            tk.Label(icon_f, image=wallet_img, bg=BG_WHITE).pack()
        else:
            tk.Frame(icon_f, bg=color, width=50, height=44).pack()

        det = tk.Frame(card, bg=BG_WHITE)
        det.pack(side="left", fill="x", expand=True)

        tk.Label(det, text=name, bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(9, "semibold"),
                 anchor="w").pack(anchor="w")
        tk.Label(det, text="Balance", bg=BG_WHITE,
                 fg="#777777", font=font(8, "medium"),
                 anchor="w").pack(anchor="w")

        pb_frame = tk.Frame(det, bg="#F1F1F1", height=8)
        pb_frame.pack(fill="x", pady=(6, 4))
        pb_frame.pack_propagate(False)

        def _draw_bar(event, bal=balance, frm=pb_frame, c=color):
            w = frm.winfo_width()
            if w < 4:
                return
            pct = min(max(bal / 50000, 0), 1) if bal > 0 else 0
            fill_w = int(w * pct)
            for child in frm.winfo_children():
                child.destroy()
            if fill_w > 0:
                tk.Frame(frm, bg=c, width=fill_w, height=8).place(x=0, y=0)

        pb_frame.bind("<Configure>", _draw_bar)

        tk.Label(det, text=f"₱{balance:,.2f}", bg=BG_WHITE,
                 fg=color, font=font(10, "semibold"),
                 anchor="w").pack(anchor="w")

    # ── Transaction History panel ─────────────────────────────────────
    def _build_history(self, parent, transactions):
        col = tk.Frame(parent, bg=BG_WHITE)
        col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(col, text="Transaction History", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(11, "medium")).pack(anchor="w", pady=(0, 8))

        scroll_outer = tk.Frame(col, bg=BG_WHITE,
                                highlightbackground=DIVIDER,
                                highlightthickness=1)
        scroll_outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_outer, bg=BG_WHITE,
                           bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(scroll_outer, orient="vertical",
                           command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_WHITE)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _scroll(e):
            try:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _scroll)
        canvas.bind("<Destroy>",
                    lambda e: canvas.unbind_all("<MouseWheel>")
                    if e.widget is canvas else None)

        if not transactions:
            tk.Label(inner, text="No transactions yet.",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(9)).pack(pady=20)
            return

        for t in transactions:
            date = t.get("date_issued", "")[:10]
            desc = t.get("description") or t.get("particulars") or "—"
            amt  = t["price"] * t["quantity"]
            kind = t["kind"]
            if kind == "expense":
                amt = -amt
            cat = t.get("income_type") or t.get("particulars") or kind.capitalize()
            self._tx_item(inner, date, desc, cat, amt)

    def _tx_item(self, parent, date, desc, cat, amount):
        item = tk.Frame(parent, bg=BG_WHITE,
                        highlightbackground="#ECDDC6",
                        highlightthickness=1,
                        padx=12, pady=10)
        item.pack(fill="x", pady=4, padx=4)

        info = tk.Frame(item, bg=BG_WHITE)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=desc, bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(9, "semibold"),
                 anchor="w").pack(anchor="w")
        tk.Label(info, text=cat, bg=BG_WHITE,
                 fg=TEXT_MUTED, font=font(8),
                 anchor="w").pack(anchor="w")
        tk.Label(info, text=date, bg=BG_WHITE,
                 fg="#999999", font=font(7),
                 anchor="w").pack(anchor="w")

        color = INCOME_GREEN if amount >= 0 else EXPENSE_RED
        sign  = "+" if amount >= 0 else "-"
        tk.Label(item,
                 text=f"{sign}₱{abs(amount):,.2f}",
                 bg=BG_WHITE, fg=color,
                 font=font(10, "semibold")).pack(side="right")