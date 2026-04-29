import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
"""
history_screen.py – Transaction history with month navigation
"""
import tkinter as tk
from constants import *
from widgets import RoundedButton, ScrollableFrame, TransactionRow


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

SAMPLE_DATA = {
    "February 2025": [
        # (date, desc, amount, cat, type)
        ("FEB 14", "FEB FAIR – Ticket Sales",   500.00, "Income",  "income"),
        ("FEB 14", "FEB FAIR – Supplies",       -320.00, "Expense", "expense"),
        ("FEB 14", "FEB FAIR – Sound System",   -200.00, "Expense", "expense"),
        ("FEB 10", "OUTREACH – Donations",      1200.00, "Income",  "income"),
        ("FEB 10", "OUTREACH – Transport",      -450.00, "Expense", "expense"),
        ("FEB  5", "GENERAL FUND – Dues",        800.00, "Income",  "income"),
        ("FEB  3", "PRINTING – Tarpaulins",     -175.00, "Expense", "expense"),
        ("FEB  1", "OPENING – Registration",     300.00, "Income",  "income"),
        ("FEB  1", "OPENING – Decorations",     -260.00, "Expense", "expense"),
    ],
    "January 2025": [
        ("JAN 28", "Planning – Venue Booking", -500.00, "Expense", "expense"),
        ("JAN 20", "Fundraiser – Raffle",       750.00, "Income",  "income"),
        ("JAN 15", "Membership – Dues",         600.00, "Income",  "income"),
        ("JAN 10", "Office – Supplies",        -120.00, "Expense", "expense"),
    ],
}


class HistoryScreen(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._months  = list(SAMPLE_DATA.keys())
        self._idx     = 0
        self._filter  = "All"   # All | Income | Expense
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_CREAM, padx=28, pady=18)
        hdr.pack(fill="x")
        new_btn = tk.Frame(hdr, bg=PRIMARY, cursor="hand2", padx=14, pady=6)
        new_btn.pack(side="right")
        tk.Label(new_btn, text="+ New", bg=PRIMARY,
                 fg="white", font=font(9, "bold")).pack()

        tk.Label(hdr, text="Transaction History", bg=BG_CREAM,
                 fg=TEXT_DARK, font=font(18, "bold")).pack(anchor="w")

        # ── Card ──────────────────────────────────────────────────────
        card = tk.Frame(self, bg=BG_WHITE, padx=22, pady=18)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        # Month navigator
        nav = tk.Frame(card, bg=BG_WHITE)
        nav.pack(fill="x", pady=(0, 12))

        tk.Label(nav, text="◀", bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(11), cursor="hand2").pack(side="left", padx=6)
        self._month_lbl = tk.Label(nav, text=self._months[self._idx],
                                   bg=BG_WHITE, fg=TEXT_DARK,
                                   font=font(11, "bold"), width=18)
        self._month_lbl.pack(side="left")
        tk.Label(nav, text="▶", bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(11), cursor="hand2").pack(side="left", padx=6)

        nav.winfo_children()[0].bind(
            "<Button-1>", lambda e: self._change_month(-1))
        nav.winfo_children()[2].bind(
            "<Button-1>", lambda e: self._change_month(+1))

        # Filter tabs (Income / Expense)
        tabs = tk.Frame(card, bg=BG_WHITE)
        tabs.pack(fill="x", pady=(0, 12))

        self._tab_btns = {}
        for label in ("All", "Income", "Expense"):
            btn = tk.Label(tabs, text=label,
                           bg=BG_CREAM, fg=TEXT_DARK,
                           font=font(9, "bold"),
                           padx=20, pady=5,
                           cursor="hand2")
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>",
                     lambda e, l=label: self._set_filter(l))
            self._tab_btns[label] = btn

        # Transaction list
        self._list_frame = tk.Frame(card, bg=BG_WHITE)
        self._list_frame.pack(fill="both", expand=True)

        self._set_filter("All")

    # ── helpers ──────────────────────────────────────────────────────
    def _change_month(self, delta):
        self._idx = (self._idx + delta) % len(self._months)
        self._month_lbl.config(text=self._months[self._idx])
        self._refresh_list()

    def _set_filter(self, label):
        self._filter = label
        for lbl, btn in self._tab_btns.items():
            if lbl == label:
                btn.config(bg=AMBER, fg="white")
            else:
                btn.config(bg=BG_CREAM, fg=TEXT_DARK)
        self._refresh_list()

    def _refresh_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        month = self._months[self._idx]
        rows  = SAMPLE_DATA.get(month, [])

        if self._filter != "All":
            rows = [r for r in rows
                    if r[4].lower() == self._filter.lower()]

        sf = ScrollableFrame(self._list_frame, bg=BG_WHITE)
        sf.pack(fill="both", expand=True)

        if not rows:
            tk.Label(sf.inner, text="No transactions this month.",
                     bg=BG_WHITE, fg=TEXT_MUTED,
                     font=font(10)).pack(pady=30)
            return

        for date, desc, amt, cat, _ in rows:
            TransactionRow(sf.inner,
                           date=date, description=desc,
                           amount=amt, category=cat,
                           bg=BG_WHITE).pack(fill="x")
