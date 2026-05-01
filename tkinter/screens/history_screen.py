import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

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

    def _build(self):
        outer = tk.Frame(self, bg=BG_CREAM, padx=20, pady=16)
        outer.pack(fill="both", expand=True)
        self._box = tk.Frame(outer, bg=BG_WHITE, padx=36, pady=28)
        self._box.pack(fill="both", expand=True)

        # title
        tk.Label(self._box, text="Transaction History", bg=BG_WHITE,
                 fg=TEXT_DARK, font=("Georgia", 22, "italic")).pack(anchor="w", pady=(0, 6))

        # month selector
        nav_row = tk.Frame(self._box, bg=BG_WHITE)
        nav_row.pack(pady=(10, 0))

        prev = tk.Label(nav_row, text="‹", bg=_MONTH_NAV_BG, fg=TEXT_DARK,
                        font=font(18), width=3, cursor="hand2")
        prev.pack(side="left", padx=(0, 8))
        prev.bind("<Button-1>", lambda e: self._change_month(-1))
        prev.bind("<Enter>",    lambda e: prev.config(bg=_MONTH_NAV_HOV, fg="white"))
        prev.bind("<Leave>",    lambda e: prev.config(bg=_MONTH_NAV_BG,  fg=TEXT_DARK))

        self._month_lbl = tk.Label(nav_row, text=self._month_str(),
                                   bg=_MONTH_BG, fg=TEXT_DARK,
                                   font=font(11, "bold"), padx=28, pady=8)
        self._month_lbl.pack(side="left")

        nxt = tk.Label(nav_row, text="›", bg=_MONTH_NAV_BG, fg=TEXT_DARK,
                       font=font(18), width=3, cursor="hand2")
        nxt.pack(side="left", padx=(8, 0))
        nxt.bind("<Button-1>", lambda e: self._change_month(+1))
        nxt.bind("<Enter>",    lambda e: nxt.config(bg=_MONTH_NAV_HOV, fg="white"))
        nxt.bind("<Leave>",    lambda e: nxt.config(bg=_MONTH_NAV_BG,  fg=TEXT_DARK))

        # filter tabs
        flt_row = tk.Frame(self._box, bg=BG_WHITE)
        flt_row.pack(pady=(18, 0))
        self._filter_btns = {}
        for key, label in [("all","All"), ("income","Income"), ("expense","Expense")]:
            btn = tk.Label(flt_row, text=label, bg=BG_WHITE, fg=TEXT_DARK,
                           font=font(10), padx=24, pady=8, cursor="hand2",
                           highlightbackground=_FILTER_BORDER, highlightthickness=2)
            btn.pack(side="left", padx=6)
            btn.bind("<Button-1>", lambda e, k=key: self._set_filter(k))
            btn.bind("<Enter>",    lambda e, b=btn, k=key: b.config(bg=_FILTER_HOV) if k != self._filter else None)
            btn.bind("<Leave>",    lambda e, b=btn, k=key: b.config(bg=_FILTER_ACTIVE if k == self._filter else BG_WHITE))
            self._filter_btns[key] = btn
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
                    lambda e: canvas.unbind_all("<MouseWheel>") if e.widget is canvas else None)

        if not rows:
            tk.Label(inner, text="No transactions found.",
                     bg=BG_WHITE, fg=TEXT_DARK, font=font(12, "bold")).pack(pady=20)
            tk.Label(inner, text="Try a different month or filter.",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(9)).pack()
            return

        for t in rows:
            self._tx_card(inner, t)

    def _tx_card(self, parent, t):
        # match web: wallet name as title, price x qty (total) - type - desc as body
        date   = t.get("date_issued", "")[:10]
        wallet = (t.get("wallet_name") or "").upper()
        qty    = t["quantity"]
        price  = t["price"]
        total  = qty * price
        kind   = t["kind"]
        desc   = t.get("description") or ""

        if kind == "income":
            type_label = t.get("income_type") or ""
            label_core = f"{price} x {qty} ({total}) - {type_label}"
        else:
            particulars = t.get("particulars") or ""
            label_core  = f"{qty} x {price} ({total}) - {particulars}"

        main_label = f"{label_core} - {desc}" if desc else label_core

        color   = _INCOME_CLR if kind == "income" else _EXPENSE_CLR
        amt_str = f"PHP {total:,.2f}" if kind == "income" else f"-PHP {total:,.2f}"

        card = tk.Frame(parent, bg=BG_WHITE,
                        highlightbackground="#ECDDC6",
                        highlightthickness=1, padx=16, pady=12)
        card.pack(fill="x", pady=5, padx=2)
        card.bind("<Enter>", lambda e: card.config(highlightbackground="#E59E2C"))
        card.bind("<Leave>", lambda e: card.config(highlightbackground="#ECDDC6"))

        left = tk.Frame(card, bg=BG_WHITE)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(left, text=wallet, bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(10, "bold"), anchor="w").pack(anchor="w")
        tk.Label(left, text=main_label, bg=BG_WHITE, fg=TEXT_MUTED,
                 font=font(8), anchor="w").pack(anchor="w")
        tk.Label(left, text=date, bg=BG_WHITE, fg="#999999",
                 font=font(7), anchor="w").pack(anchor="w")

        tk.Label(card, text=amt_str, bg=BG_WHITE, fg=color,
                 font=font(11, "bold")).pack(side="right", anchor="center")

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
        self._month_lbl.config(text=self._month_str())
        self._refresh()

    def _set_filter(self, key):
        self._filter = key
        self._update_filter_styles()
        self._refresh()

    def _update_filter_styles(self):
        for k, btn in self._filter_btns.items():
            if k == self._filter:
                btn.config(bg=_FILTER_ACTIVE, fg="white",
                           highlightbackground=_FILTER_ACTIVE)
            else:
                btn.config(bg=BG_WHITE, fg=TEXT_DARK,
                           highlightbackground=_FILTER_BORDER)
