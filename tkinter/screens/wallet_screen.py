import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
"""
wallet_screen.py – Wallet overview + wallet detail (Transactions / Reports / Receipts)
"""
import tkinter as tk
from constants import *
from widgets import ScrollableFrame, TransactionRow
import os
from PIL import Image, ImageTk


WALLETS = [
    {"name": "Feb Fair",     "balance": 10500.00, "color": AMBER},
    {"name": "Outreach",     "balance":  6820.00, "color": PRIMARY},
    {"name": "Gen Fund",     "balance": 12680.00, "color": INCOME_GREEN},
    {"name": "Sports Fest",  "balance":  3200.00, "color": "#9B6FCF"},
    {"name": "Acquaintance", "balance":  1500.00, "color": "#E05C5C"},
    {"name": "Leadership",   "balance":  5000.00, "color": "#4AA8D8"},
]

WALLET_TRANSACTIONS = {
    "Feb Fair": [
        ("FEB 14", "Ticket Sales",   500.00,   "Income"),
        ("FEB 14", "Sound System",  -200.00,   "Expense"),
        ("FEB 14", "Supplies",      -320.00,   "Expense"),
        ("FEB 12", "Sponsorship",   1000.00,   "Income"),
        ("FEB 10", "Venue Deposit", -500.00,   "Expense"),
    ],
    "Outreach": [
        ("FEB 10", "Donations",     1200.00,   "Income"),
        ("FEB 10", "Transport",     -450.00,   "Expense"),
        ("FEB  8", "Food Packs",    -780.00,   "Expense"),
    ],
}


class WalletScreen(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._selected = None
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_CREAM, padx=28, pady=18)
        hdr.pack(fill="x")
        new_btn = tk.Frame(hdr, bg=PRIMARY, cursor="hand2", padx=14, pady=6)
        new_btn.pack(side="right")
        tk.Label(new_btn, text="+ New", bg=PRIMARY,
                 fg="white", font=font(9, "bold")).pack()
        tk.Label(hdr, text="Wallet", bg=BG_CREAM,
                 fg=TEXT_DARK, font=font(18, "bold")).pack(anchor="w")

        # ── Wallet grid ───────────────────────────────────────────────
        grid_area = tk.Frame(self, bg=BG_CREAM, padx=28)
        grid_area.pack(fill="x")

        self._wallet_img = self._load_wallet_icon()
        cols = 4
        for i, w in enumerate(WALLETS):
            row_i, col_i = divmod(i, cols)
            card = tk.Frame(grid_area, bg=BG_WHITE,
                            padx=14, pady=12,
                            cursor="hand2", relief="flat")
            card.grid(row=row_i, column=col_i,
                      padx=6, pady=6, sticky="nsew")
            grid_area.columnconfigure(col_i, weight=1)

            # coloured top strip
            strip = tk.Frame(card, bg=w["color"], height=5)
            strip.pack(fill="x")

            if self._wallet_img:
                tk.Label(card, image=self._wallet_img,
                         bg=BG_WHITE).pack(pady=4)

            tk.Label(card, text=w["name"], bg=BG_WHITE,
                     fg=TEXT_DARK, font=font(9, "bold")).pack()
            tk.Label(card, text=f"₱{w['balance']:,.2f}",
                     bg=BG_WHITE, fg=w["color"],
                     font=font(10, "bold")).pack()

            card.bind("<Button-1>",
                      lambda e, name=w["name"]: self._open_wallet(name))
            for child in card.winfo_children():
                child.bind("<Button-1>",
                           lambda e, name=w["name"]: self._open_wallet(name))

        # ── Detail panel (shown when wallet is selected) ───────────────
        self._detail = tk.Frame(self, bg=BG_WHITE, padx=20, pady=16)
        # not packed yet – shown on wallet click

    def _load_wallet_icon(self, size=40):
        path = os.path.join(ASSETS_DIR, "wallet.png")
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path).resize((size, size), Image.LANCZOS)
            ph  = ImageTk.PhotoImage(img)
            self._ph_wallet = ph
            return ph
        except Exception:
            return None

    def _open_wallet(self, name):
        # remove any existing detail
        self._detail.pack_forget()
        for w in self._detail.winfo_children():
            w.destroy()
        self._detail.pack(fill="both", expand=True,
                          padx=28, pady=(0, 20))

        # header
        hdr = tk.Frame(self._detail, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="◀", bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(11), cursor="hand2").pack(side="left")
        tk.Label(hdr, text=name, bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(13, "bold")).pack(
                     side="left", padx=10)

        # tabs
        tab_frame = tk.Frame(self._detail, bg=BG_WHITE)
        tab_frame.pack(fill="x")
        self._tab_frames = {}
        self._tab_buttons = {}

        for tab in ("Transactions", "Reports", "Receipts"):
            btn = tk.Label(tab_frame, text=tab,
                           bg=BG_CREAM, fg=TEXT_DARK,
                           font=font(9, "bold"),
                           padx=16, pady=5, cursor="hand2")
            btn.pack(side="left", padx=3)
            self._tab_buttons[tab] = btn
            btn.bind("<Button-1>",
                     lambda e, t=tab, n=name: self._switch_tab(t, n))

        self._content = tk.Frame(self._detail, bg=BG_WHITE)
        self._content.pack(fill="both", expand=True, pady=10)

        self._switch_tab("Transactions", name)

    def _switch_tab(self, tab, wallet_name):
        for t, btn in self._tab_buttons.items():
            btn.config(bg=AMBER if t == tab else BG_CREAM,
                       fg="white" if t == tab else TEXT_DARK)
        for w in self._content.winfo_children():
            w.destroy()

        if tab == "Transactions":
            self._show_transactions(wallet_name)
        elif tab == "Reports":
            self._show_reports(wallet_name)
        elif tab == "Receipts":
            self._show_receipts(wallet_name)

    def _show_transactions(self, name):
        rows = WALLET_TRANSACTIONS.get(name, [])

        # income/expense filter
        flt = tk.Frame(self._content, bg=BG_WHITE)
        flt.pack(fill="x", pady=(0, 8))
        for label in ("Income", "Expense"):
            tk.Label(flt, text=label, bg=AMBER if label == "Income" else BG_CREAM,
                     fg="white" if label == "Income" else TEXT_DARK,
                     font=font(8, "bold"),
                     padx=14, pady=4, cursor="hand2").pack(side="left", padx=3)

        sf = ScrollableFrame(self._content, bg=BG_WHITE)
        sf.pack(fill="both", expand=True)

        if not rows:
            tk.Label(sf.inner, text="No transactions yet.",
                     bg=BG_WHITE, fg=TEXT_MUTED,
                     font=font(9)).pack(pady=20)
            return

        for date, desc, amt, cat in rows:
            TransactionRow(sf.inner,
                           date=date, description=desc,
                           amount=amt, category=cat,
                           bg=BG_WHITE).pack(fill="x")

    def _show_reports(self, name):
        card = tk.Frame(self._content, bg=AMBER_BG, padx=16, pady=14)
        card.pack(fill="x", padx=4, pady=4)
        top = tk.Frame(card, bg=AMBER_BG)
        top.pack(fill="x")
        tk.Label(top, text="📄  Generate Financial Report",
                 bg=AMBER_BG, fg=TEXT_DARK,
                 font=font(10, "bold")).pack(side="left")

        btns = tk.Frame(card, bg=AMBER_BG)
        btns.pack(anchor="e")
        for lbl, c in [("Preview", AMBER), ("PDF", EXPENSE_RED)]:
            b = tk.Frame(btns, bg=c, padx=10, pady=4,
                         cursor="hand2")
            b.pack(side="left", padx=4)
            tk.Label(b, text=lbl, bg=c, fg="white",
                     font=font(8, "bold")).pack()

        tk.Label(card,
                 text=f"Creates an Activity Financial Statement for {name} 2025.",
                 bg=AMBER_BG, fg=TEXT_MUTED, font=font(8)).pack(
                     anchor="w", pady=(4, 10))

        stats = tk.Frame(card, bg=AMBER_BG)
        stats.pack(fill="x")
        for label, val in [("Budget", "₱15,000"), ("Total income", "₱12,700"),
                           ("Total expense", "₱8,250"), ("Net", "₱4,450")]:
            col = tk.Frame(stats, bg=BG_WHITE, padx=12, pady=8)
            col.pack(side="left", padx=4, expand=True, fill="x")
            tk.Label(col, text=label, bg=BG_WHITE,
                     fg=TEXT_MUTED, font=font(7)).pack(anchor="w")
            tk.Label(col, text=val, bg=BG_WHITE,
                     fg=TEXT_DARK, font=font(10, "bold")).pack(anchor="w")

    def _show_receipts(self, name):
        grid = tk.Frame(self._content, bg=BG_WHITE)
        grid.pack(fill="both", expand=True)
        for i in range(4):
            card = tk.Frame(grid, bg=BG_CARD,
                            padx=16, pady=16, relief="flat")
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            grid.columnconfigure(i, weight=1)
            tk.Label(card, text="📄", bg=BG_CARD,
                     font=font(22)).pack(pady=4)
            tk.Label(card, text=f"Receipt {i+1:02d}.pdf",
                     bg=BG_CARD, fg=TEXT_DARK,
                     font=font(8)).pack()
            row = tk.Frame(card, bg=BG_CARD)
            row.pack()
            for lbl, c in [("Download", AMBER), ("Delete", EXPENSE_RED)]:
                b = tk.Frame(row, bg=c, padx=6, pady=2, cursor="hand2")
                b.pack(side="left", padx=2)
                tk.Label(b, text=lbl, bg=c, fg="white",
                         font=font(7)).pack()
