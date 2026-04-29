import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from constants import *
from widgets import SummaryCard, TransactionRow, ScrollableFrame
from datetime import datetime
from db import get_home_data

WALLET_COLORS = [AMBER, PRIMARY, INCOME_GREEN, "#9B6FCF", "#4AA8D8", "#E05C5C"]


class HomeScreen(tk.Frame):
    def __init__(self, parent, org=None, **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._org = org or {}
        self._data = {}
        self._build()

    def _build(self):
        # loading indicator while fetching
        loading = tk.Label(self, text="Loading...", bg=BG_CREAM,
                           fg=TEXT_MUTED, font=font(11))
        loading.pack(expand=True)
        self.update()

        try:
            self._data = get_home_data(self._org.get("id"))
        except Exception:
            self._data = {
                "total_balance": 0, "total_wallets": 0,
                "income_month": 0, "expense_month": 0,
                "wallets": [], "transactions": [], "wallet_map": {}
            }

        loading.destroy()
        self._render()

    def _render(self):
        d = self._data
        org_name = self._org.get("org_name", "Organization")
        date_str = datetime.now().strftime("%A, %B %d")

        # ── Header ────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_CREAM, padx=28, pady=18)
        hdr.pack(fill="x")

        # Large italic greeting
        greeting = tk.Label(hdr, text=f"Hello, {org_name} part 2", bg=BG_CREAM,
                    fg=TEXT_DARK, font=(FONT_FAMILY, 22, "italic"))
        greeting.pack(anchor="w")

        # Date
        tk.Label(hdr, text=date_str, bg=BG_CREAM,
             fg=TEXT_MUTED, font=font(10)).pack(anchor="w")

        # Search and profile (right)
        # (You may add widgets here if needed)

        # ── Summary cards ─────────────────────────────────────────────
        summary = tk.Frame(self, bg=BG_CREAM, padx=28)
        summary.pack(fill="x", pady=(0, 18))

        # Card-style summary with rounded corners
        card_bg = "#F6D7A7"
        card = tk.Frame(summary, bg=card_bg, bd=0, relief="flat", padx=18, pady=18)
        card.pack(fill="x", expand=True)
        card.grid_columnconfigure((0,1,2,3), weight=1)

        # Card items
        items = [
            ("Total Balance",       f"₱{d['total_balance']:,.2f}"),
            ("Income this April",   f"₱{d['income_month']:,.2f}"),
            ("Expenses this April", f"₱{d['expense_month']:,.2f}"),
            ("Reports submitted",   str(d.get("reports", 4)))
        ]
        colors = [AMBER_BG, "#E8F5EE", "#FDECEA", "#F0EAF8"]
        accents = [AMBER, INCOME_GREEN, EXPENSE_RED, "#9B6FCF"]
        for i, (lbl, val) in enumerate(items):
            f = tk.Frame(card, bg=colors[i], padx=10, pady=10, bd=0, relief="flat")
            f.grid(row=0, column=i, sticky="nsew", padx=10)
            tk.Label(f, text=lbl, bg=colors[i], fg=TEXT_LABEL, font=font(9)).pack(anchor="w")
            tk.Label(f, text=val, bg=colors[i], fg=accents[i], font=font(13, "bold")).pack(anchor="w", pady=(4,0))

        # ── Body ──────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG_CREAM, padx=28)
        body.pack(fill="both", expand=True)

        # Wallets Overview (left)
        wallets_card = tk.Frame(body, bg=BG_WHITE, padx=18, pady=18, bd=0, relief="flat")
        wallets_card.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=4)
        tk.Label(wallets_card, text="Wallets Overview", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(12, "bold"), anchor="w").pack(fill="x", pady=(0, 12))
        if not d["wallets"]:
            tk.Label(wallets_card, text="No wallets found.", bg=BG_WHITE,
                     fg=TEXT_MUTED, font=font(9)).pack(pady=10)
        else:
            for i, (name, balance) in enumerate(d["wallets"]):
                color = WALLET_COLORS[i % len(WALLET_COLORS)]
                row = tk.Frame(wallets_card, bg=BG_CARD, padx=14, pady=10)
                row.pack(fill="x", pady=6)
                # Icon placeholder (replace with wallet icon if available)
                dot = tk.Frame(row, bg=color, width=32, height=32)
                dot.pack(side="left")
                dot.pack_propagate(False)
                tk.Label(row, text=name, bg=BG_CARD,
                         fg=TEXT_DARK, font=font(10, "bold"), anchor="w").pack(side="left", padx=10)
                tk.Label(row, text=f"₱{balance:,.2f}", bg=BG_CARD,
                         fg=color, font=font(11, "bold")).pack(side="right")

        # Transaction History (right)
        history_card = tk.Frame(body, bg=BG_WHITE, padx=18, pady=18, bd=0, relief="flat")
        history_card.pack(side="right", fill="both", expand=True, padx=(12, 0), pady=4)
        tk.Label(history_card, text="Transaction History", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(12, "bold")).pack(anchor="w")
        # Scrollable area for transactions
        sf = ScrollableFrame(history_card, bg=BG_WHITE)
        sf.pack(fill="both", expand=True, pady=(10,0))
        if not d["transactions"]:
            tk.Label(sf.inner, text="No transactions yet.", bg=BG_WHITE,
                     fg=TEXT_MUTED, font=font(9)).pack(pady=20)
        else:
            for t in d["transactions"]:
                date = t.get("date_issued", "")[:10]
                desc = t.get("description") or t.get("particulars") or "—"
                amt  = t["price"] * t["quantity"]
                if t["kind"] == "expense":
                    amt = -amt
                cat  = t.get("income_type") or t.get("particulars") or t["kind"].capitalize()
                TransactionRow(sf.inner, date=date, description=desc,
                               amount=amt, category=cat,
                               bg=BG_WHITE).pack(fill="x", pady=2)

    def _build_wallets(self, parent, wallets):
        col = tk.Frame(parent, bg=BG_WHITE, padx=16, pady=14)
        col.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=4)

        tk.Label(col, text="Wallets Overview", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(11, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 10))

        if not wallets:
            tk.Label(col, text="No wallets found.", bg=BG_WHITE,
                     fg=TEXT_MUTED, font=font(9)).pack(pady=10)
            return

        for i, (name, balance) in enumerate(wallets):
            color = WALLET_COLORS[i % len(WALLET_COLORS)]
            row = tk.Frame(col, bg=BG_CARD, padx=14, pady=10)
            row.pack(fill="x", pady=4)

            dot = tk.Frame(row, bg=color, width=10, height=10)
            dot.pack(side="left")
            dot.pack_propagate(False)

            tk.Label(row, text=name, bg=BG_CARD,
                     fg=TEXT_DARK, font=font(9),
                     anchor="w").pack(side="left", padx=10)
            tk.Label(row, text=f"₱{balance:,.2f}", bg=BG_CARD,
                     fg=color, font=font(10, "bold")).pack(side="right")

    def _build_history(self, parent, transactions, wallet_map):
        col = tk.Frame(parent, bg=BG_WHITE, padx=16, pady=14)
        col.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=4)

        hdr = tk.Frame(col, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="Transaction History", bg=BG_WHITE,
                 fg=TEXT_DARK, font=font(11, "bold")).pack(side="left")
        tk.Label(hdr, text="See all →", bg=BG_WHITE,
                 fg=AMBER, font=font(8), cursor="hand2").pack(side="right")

        ch = tk.Frame(col, bg=BG_WHITE)
        ch.pack(fill="x", pady=(0, 4))
        for h, w, anchor in [("Date", 10, "w"), ("Description", 0, "w"),
                              ("Category", 12, "w"), ("Amount", 12, "e")]:
            tk.Label(ch, text=h, bg=BG_WHITE, fg=TEXT_MUTED, font=font(8),
                     width=w, anchor=anchor).pack(
                side="left" if anchor == "w" else "right",
                expand=(w == 0), fill="x" if w == 0 else None)

        sf = ScrollableFrame(col, bg=BG_WHITE)
        sf.pack(fill="both", expand=True)

        if not transactions:
            tk.Label(sf.inner, text="No transactions yet.", bg=BG_WHITE,
                     fg=TEXT_MUTED, font=font(9)).pack(pady=20)
            return

        for t in transactions:
            date = t.get("date_issued", "")[:10]
            desc = t.get("description") or t.get("particulars") or "—"
            amt  = t["price"] * t["quantity"]
            if t["kind"] == "expense":
                amt = -amt
            cat  = t.get("income_type") or t.get("particulars") or t["kind"].capitalize()
            TransactionRow(sf.inner, date=date, description=desc,
                           amount=amt, category=cat,
                           bg=BG_WHITE).pack(fill="x")
