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

        # ── white content box (matches .content-box) ──────────────────
        outer = tk.Frame(self, bg=BG_CREAM, padx=20, pady=16)
        outer.pack(fill="both", expand=True)

        box = tk.Frame(outer, bg=BG_WHITE, padx=30, pady=24)
        box.pack(fill="both", expand=True)

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
        banner = tk.Frame(box, bg="#E59E2C", padx=20, pady=16)
        banner.pack(fill="x", pady=(14, 0))

        summary_items = [
            ("Total Balance",            f"₱{d['total_balance']:,.2f}"),
            (f"Income this {month_lbl}", f"₱{d['income_month']:,.2f}"),
            (f"Expenses this {month_lbl}",f"₱{d['expense_month']:,.2f}"),
            ("Reports submitted",         str(d.get("reports", 0))),
        ]
        for i, (lbl, val) in enumerate(summary_items):
            card = tk.Frame(banner, bg="white", padx=14, pady=10)
            card.grid(row=0, column=i, sticky="nsew", padx=8)
            banner.columnconfigure(i, weight=1)
            tk.Label(card, text=lbl, bg="white",
                     fg="#555555", font=font(8)).pack(anchor="w")
            tk.Label(card, text=val, bg="white",
                     fg=TEXT_DARK, font=font(12, "bold")).pack(anchor="w", pady=(4, 0))

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
                 fg=TEXT_DARK, font=font(11, "bold")).pack(anchor="w", pady=(0, 8))

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

        # icon
        icon_f = tk.Frame(card, bg=BG_WHITE)
        icon_f.pack(side="left", padx=(0, 12))
        if wallet_img:
            tk.Label(icon_f, image=wallet_img, bg=BG_WHITE).pack()
        else:
            tk.Frame(icon_f, bg=color, width=50, height=44).pack()

        # details
        det = tk.Frame(card, bg=BG_WHITE)
        det.pack(side="left", fill="x", expand=True)

        tk.Label(det, text=name, bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(9, "bold"),
                 anchor="w").pack(anchor="w")
        tk.Label(det, text="Balance", bg=BG_WHITE,
                 fg="#777777", font=font(8),
                 anchor="w").pack(anchor="w")

        # progress bar (visual only, fills based on positive balance ratio)
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

        # balance label
        tk.Label(det, text=f"₱{balance:,.2f}", bg=BG_WHITE,
                 fg=color, font=font(10, "bold"),
                 anchor="w").pack(anchor="w")

    # ── Transaction History panel ─────────────────────────────────────
    def _build_history(self, parent, transactions):
        col = tk.Frame(parent, bg=BG_WHITE)
        col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(col, text="Transaction History", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(11, "bold")).pack(anchor="w", pady=(0, 8))

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

        # left: description + category + date
        info = tk.Frame(item, bg=BG_WHITE)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=desc, bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(9, "bold"),
                 anchor="w").pack(anchor="w")
        tk.Label(info, text=cat, bg=BG_WHITE,
                 fg=TEXT_MUTED, font=font(8),
                 anchor="w").pack(anchor="w")
        tk.Label(info, text=date, bg=BG_WHITE,
                 fg="#999999", font=font(7),
                 anchor="w").pack(anchor="w")

        # right: amount
        color = INCOME_GREEN if amount >= 0 else EXPENSE_RED
        sign  = "+" if amount >= 0 else "-"
        tk.Label(item,
                 text=f"{sign}₱{abs(amount):,.2f}",
                 bg=BG_WHITE, fg=color,
                 font=font(10, "bold")).pack(side="right")
