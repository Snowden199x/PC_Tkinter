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


def _load_img_rounded(name, w, h, radius, cache):
    """Load image with rounded corners using a PIL mask."""
    path = _os.path.join(_ASSETS, name)
    if not _os.path.exists(path):
        return None
    try:
        from PIL import ImageDraw
        img = Image.open(path).resize((w, h), Image.LANCZOS).convert("RGBA")
        # composite onto white background so corners are white, not transparent/black
        bg = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
        bg.paste(img, mask=mask)
        ph = ImageTk.PhotoImage(bg.convert("RGB"))
        cache.append(ph)
        return ph
    except Exception:
        return _load_img(name, w, h, cache)


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
        outer = tk.Frame(self, bg=BG_CREAM)
        outer.pack(fill="both", expand=True, padx=12, pady=(0, 16))

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
            # exact gradient color at card center (no blending) for canvas bg
            exact_bg = "#{:02x}{:02x}{:02x}".format(*base)
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
            cv.config(bg=exact_bg)  # match exact gradient so corners are invisible
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

        self._build_wallets(overview, d.get("wallets_overview", []))
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
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        wallet_img = _load_img_rounded("wallet.png", 64, 56, 7, self._imgs)

        if not wallets:
            frm = tk.Frame(inner, bg=BG_WHITE)
            frm.pack(expand=True, pady=30)
            ico = _load_img("navi_wallet.png", 40, 40, self._imgs)
            if ico:
                tk.Label(frm, image=ico, bg=BG_WHITE).pack(pady=(0, 8))
            tk.Label(frm, text="No wallets yet", bg=BG_WHITE,
                     fg=TEXT_DARK, font=font(10, "bold")).pack()
            tk.Label(frm, text="Create your first wallet to start tracking",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(8)).pack(pady=(4, 0))
        else:
            for folder in wallets:
                self._wallet_card(inner, folder, wallet_img)

    def _wallet_card(self, parent, folder, wallet_img):
        name          = folder.get("name", "—")
        budget        = float(folder.get("budget", 0))
        total_income  = float(folder.get("total_income", 0))
        total_expense = float(folder.get("total_expenses", 0))
        used          = total_expense
        progress      = min((used / budget * 100) if budget > 0 else 0, 100)

        # show month only — strip " – WalletName" suffix if present
        month_only = name.split(" – ")[0].strip() if " – " in name else name

        card = tk.Frame(parent, bg=BG_WHITE,
                        highlightbackground="#F0E6D5",
                        highlightthickness=1,
                        padx=14, pady=12)
        card.pack(fill="x", pady=5, padx=4)

        # icon
        icon_f = tk.Frame(card, bg=BG_WHITE)
        icon_f.pack(side="left", padx=(0, 12))
        if wallet_img:
            tk.Label(icon_f, image=wallet_img, bg=BG_WHITE).pack()

        # details
        det = tk.Frame(card, bg=BG_WHITE)
        det.pack(side="left", fill="x", expand=True)

        # month name only
        tk.Label(det, text=month_only, bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(9, "bold"), anchor="w").pack(anchor="w")

        # "Budget Used" label
        tk.Label(det, text="Budget Used", bg=BG_WHITE,
                 fg=TEXT_MUTED, font=font(7), anchor="w").pack(anchor="w", pady=(3, 0))

        # progress bar
        pb_outer = tk.Frame(det, bg="#F1F1F1", height=7)
        pb_outer.pack(fill="x", pady=(3, 0))
        pb_outer.pack_propagate(False)

        def _draw_bar(event, pct=progress, frm=pb_outer):
            w = frm.winfo_width()
            if w < 4:
                return
            fill_w = int(w * pct / 100)
            for child in frm.winfo_children():
                child.destroy()
            if fill_w > 0:
                color = "#E59E2C" if pct < 90 else "#C62828"
                tk.Frame(frm, bg=color, width=fill_w, height=7).place(x=0, y=0)

        pb_outer.bind("<Configure>", _draw_bar)

        # "Php used / Php budget" right-aligned, just below the progress bar
        used_str   = f"Php {used:,.0f}"
        budget_str = f"Php {budget:,.0f}"
        tk.Label(det, text=f"{used_str} / {budget_str}",
                 bg=BG_WHITE, fg="#616161", font=font(7),
                 anchor="e").pack(fill="x", pady=(2, 4))

        # income / expense stats row
        stats = tk.Frame(det, bg=BG_WHITE)
        stats.pack(anchor="w")
        tk.Label(stats, text=f"Income: Php {total_income:,.2f}",
                 bg=BG_WHITE, fg="#2E7D32", font=font(7)).pack(side="left", padx=(0, 10))
        tk.Label(stats, text=f"Expenses: Php {total_expense:,.2f}",
                 bg=BG_WHITE, fg="#C62828", font=font(7)).pack(side="left")

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
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
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
            frm = tk.Frame(inner, bg=BG_WHITE)
            frm.pack(expand=True, pady=30)
            ico = _load_img("navi_history.png", 40, 40, self._imgs)
            if ico:
                tk.Label(frm, image=ico, bg=BG_WHITE).pack(pady=(0, 8))
            tk.Label(frm, text="No transactions yet", bg=BG_WHITE,
                     fg=TEXT_DARK, font=font(10, "bold")).pack()
            tk.Label(frm, text="Your transaction history will appear here",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(8)).pack(pady=(4, 0))
            return

        wallet_map = self._data.get("wallet_map", {})
        for t in transactions:
            self._tx_item(inner, t, wallet_map)

    def _tx_item(self, parent, t, wallet_map=None):
        """Same card format as wallet screen _tx_item."""
        date  = t.get("date_issued", "")[:10]
        desc  = t.get("description") or "—"
        qty   = t.get("quantity", 1)
        price = t.get("price", 0)
        total = qty * price
        amt   = total if t["kind"] == "income" else -total
        qty_line = f"{price:,.2f} x {qty} ({total:,.2f})"

        # wallet name as the "month label" header (since home shows across wallets)
        if wallet_map:
            header = wallet_map.get(t.get("wallet_id"), "")
        else:
            header = ""

        try:
            month_label = datetime.strptime(date, "%Y-%m-%d").strftime("%B").upper()
        except Exception:
            month_label = date

        card = tk.Frame(parent, bg=BG_WHITE,
                        highlightbackground="#ECDDC6",
                        highlightthickness=1, padx=14, pady=10)
        card.pack(fill="x", pady=4, padx=4)
        card.bind("<Enter>", lambda e: card.config(highlightbackground="#E59E2C"))
        card.bind("<Leave>", lambda e: card.config(highlightbackground="#ECDDC6"))

        left = tk.Frame(card, bg=BG_WHITE)
        left.pack(side="left", fill="x", expand=True)

        if t["kind"] == "income":
            income_type = t.get("income_type") or "—"
            tk.Label(left, text=month_label, bg=BG_WHITE, fg=TEXT_DARK,
                     font=font(9, "bold"), anchor="w").pack(anchor="w")
            tk.Label(left, text=f"{qty_line}  ·  {income_type}  ·  {desc}",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(8), anchor="w").pack(anchor="w")
        else:
            particulars = t.get("particulars") or "—"
            tk.Label(left, text=month_label, bg=BG_WHITE, fg=TEXT_DARK,
                     font=font(9, "bold"), anchor="w").pack(anchor="w")
            tk.Label(left, text=f"{qty_line}  ·  {particulars}  ·  {desc}",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(8), anchor="w").pack(anchor="w")

        # wallet name as a small tag below
        if header:
            tk.Label(left, text=header, bg=BG_WHITE, fg="#999999",
                     font=font(7), anchor="w").pack(anchor="w")
        tk.Label(left, text=date, bg=BG_WHITE, fg="#999999",
                 font=font(7), anchor="w").pack(anchor="w")

        color = INCOME_GREEN if amt >= 0 else EXPENSE_RED
        sign  = "+" if amt >= 0 else "-"
        tk.Label(card, text=f"{sign}₱{abs(amt):,.2f}",
                 bg=BG_WHITE, fg=color,
                 font=font(10, "bold")).pack(side="right", anchor="center")