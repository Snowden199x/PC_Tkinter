import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
"""
home_screen.py – Main dashboard screen
"""
import tkinter as tk
from constants import *
from widgets import SummaryCard, TransactionRow, ScrollableFrame
from datetime import datetime


SAMPLE_TRANSACTIONS = [
    ("Feb 14", "FEB FAIR – Ticket Sales",  500.00, "Income",  "Feb Fair"),
    ("Feb 14", "FEB FAIR – Supplies",     -320.00, "Expense", "Feb Fair"),
    ("Feb 10", "OUTREACH – Donations",    1200.00, "Income",  "Outreach"),
    ("Feb 10", "OUTREACH – Transport",    -450.00, "Expense", "Outreach"),
    ("Feb  5", "GENERAL FUND – Dues",      800.00, "Income",  "General"),
    ("Feb  3", "PRINTING – Tarpaulins",   -175.00, "Expense", "General"),
]

SAMPLE_WALLETS = [
    ("Feb Fair",     "₱10,500", AMBER),
    ("Outreach",     "₱6,820",  PRIMARY),
    ("General Fund", "₱12,680", INCOME_GREEN),
]


class HomeScreen(tk.Frame):
    def __init__(self, parent, org_name="Information Technology Inks, Nab.",
                 **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._org = org_name
        self._build()

    def _build(self):
        # ── Top header ────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_CREAM, padx=28, pady=18)
        hdr.pack(fill="x")

        # New button
        new_btn = tk.Frame(hdr, bg=PRIMARY, cursor="hand2",
                           padx=14, pady=6)
        new_btn.pack(side="right")
        tk.Label(new_btn, text="+ New", bg=PRIMARY,
                 fg="white", font=font(9, "bold")).pack()

        date_str = datetime.now().strftime("%A, %B %d")
        tk.Label(hdr, text=f"Hello, ITUI", bg=BG_CREAM,
                 fg=TEXT_DARK, font=font(18, "bold")).pack(anchor="w")
        tk.Label(hdr, text=date_str, bg=BG_CREAM,
                 fg=TEXT_MUTED, font=font(9)).pack(anchor="w")

        # ── Summary row ───────────────────────────────────────────────
        summary = tk.Frame(self, bg=BG_CREAM, padx=28)
        summary.pack(fill="x", pady=(0, 14))
        for lbl, val, bg, acc in [
            ("Total balance",      "₱30,000", AMBER_BG,          AMBER),
            ("Total no. of events","5",        "#F0EAF8",         "#9B6FCF"),
            ("Income this month",  "₱1,055",   "#E8F5EE",         INCOME_GREEN),
            ("Expenses this month","₱5,021",   "#FDECEA",         EXPENSE_RED),
        ]:
            SummaryCard(summary, label=lbl, value=val,
                        bg=bg, accent=acc).pack(
                side="left", expand=True, fill="both", padx=4)

        # ── Body: wallets overview + transaction history ──────────────
        body = tk.Frame(self, bg=BG_CREAM, padx=28)
        body.pack(fill="both", expand=True)

        self._build_wallets(body)
        self._build_history(body)

    def _build_wallets(self, parent):
        col = tk.Frame(parent, bg=BG_WHITE, padx=16, pady=14)
        col.pack(side="left", fill="both", expand=True,
                 padx=(0, 10), pady=4)

        tk.Label(col, text="Wallets Overview", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(11, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 10))

        for name, bal, color in SAMPLE_WALLETS:
            row = tk.Frame(col, bg=BG_CARD, padx=14, pady=10)
            row.pack(fill="x", pady=4)

            dot = tk.Frame(row, bg=color, width=10, height=10)
            dot.pack(side="left")
            dot.pack_propagate(False)

            tk.Label(row, text=name, bg=BG_CARD,
                     fg=TEXT_DARK, font=font(9),
                     anchor="w").pack(side="left", padx=10)
            tk.Label(row, text=bal, bg=BG_CARD,
                     fg=color, font=font(10, "bold")).pack(side="right")

    def _build_history(self, parent):
        col = tk.Frame(parent, bg=BG_WHITE, padx=16, pady=14)
        col.pack(side="right", fill="both", expand=True,
                 padx=(10, 0), pady=4)

        hdr = tk.Frame(col, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="Transaction History", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(11, "bold")).pack(side="left")
        tk.Label(hdr, text="See all →", bg=BG_WHITE,
                 fg=AMBER, font=font(8),
                 cursor="hand2").pack(side="right")

        # column headers
        ch = tk.Frame(col, bg=BG_WHITE)
        ch.pack(fill="x", pady=(0, 4))
        for h, w, anchor in [("Date", 10, "w"), ("Description", 0, "w"),
                              ("Category", 12, "w"), ("Amount", 12, "e")]:
            tk.Label(ch, text=h, bg=BG_WHITE,
                     fg=TEXT_MUTED, font=font(8),
                     width=w, anchor=anchor).pack(
                         side="left" if anchor == "w" else "right",
                         expand=(w == 0), fill="x" if w == 0 else None)

        sf = ScrollableFrame(col, bg=BG_WHITE)
        sf.pack(fill="both", expand=True)

        for date, desc, amt, cat, wallet in SAMPLE_TRANSACTIONS:
            TransactionRow(sf.inner,
                           date=date, description=desc,
                           amount=amt, category=cat,
                           bg=BG_WHITE).pack(fill="x")
