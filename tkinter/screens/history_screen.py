import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from constants import (
    WHITE, CREAM, AMBER, AMBER_LIGHT,
    TEXT_DARK, TEXT_MUTE, GREEN_OK, RED_ERR,
    styled_btn, supabase
)


class HistoryTab(tk.Frame):
    def __init__(self, parent, org):
        super().__init__(parent, bg=WHITE)
        self.org     = org
        self._filter = "all"
        self._year   = datetime.now().year
        self._month  = datetime.now().month
        self._build()
        self.load()

    def _build(self):
        hdr = tk.Frame(self, bg=WHITE)
        hdr.pack(fill="x", padx=30, pady=(24, 0))
        tk.Label(hdr, text="Transaction History", bg=WHITE, fg=TEXT_DARK,
                 font=("Georgia", 22, "italic")).pack(anchor="w")

        # Month navigator
        nav_row = tk.Frame(self, bg=WHITE)
        nav_row.pack(pady=10)
        styled_btn(nav_row, "‹", self._prev_month, bg=CREAM, fg=TEXT_DARK,
                   font=("Poppins", 14)).pack(side="left", padx=6)
        self._month_lbl = tk.Label(nav_row, bg=AMBER_LIGHT, fg=TEXT_DARK,
                                   font=("Poppins", 11, "bold"),
                                   width=20, pady=8, relief="flat")
        self._month_lbl.pack(side="left")
        styled_btn(nav_row, "›", self._next_month, bg=CREAM, fg=TEXT_DARK,
                   font=("Poppins", 14)).pack(side="left", padx=6)
        self._update_month_label()

        # Filter tabs
        ftab = tk.Frame(self, bg=WHITE)
        ftab.pack(pady=6)
        self._filter_btns = {}
        for f in ("all", "income", "expense"):
            b = tk.Button(ftab, text=f.capitalize(),
                          font=("Poppins", 10), relief="flat",
                          cursor="hand2", padx=20, pady=6,
                          command=lambda x=f: self._set_filter(x))
            b.pack(side="left", padx=4)
            self._filter_btns[f] = b
        self._set_filter_style("all")

        # Scrollable list
        frame = tk.Frame(self, bg=WHITE)
        frame.pack(fill="both", expand=True, padx=30, pady=4)
        canvas = tk.Canvas(frame, bg=WHITE, highlightthickness=0)
        sb     = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        self._tx_inner = tk.Frame(canvas, bg=WHITE)
        self._tx_inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._tx_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _update_month_label(self):
        months = ["", "January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        self._month_lbl.config(text=f"{months[self._month]} {self._year}")

    def _prev_month(self):
        self._month -= 1
        if self._month < 1:
            self._month = 12
            self._year -= 1
        self._update_month_label()
        self.load()

    def _next_month(self):
        self._month += 1
        if self._month > 12:
            self._month = 1
            self._year += 1
        self._update_month_label()
        self.load()

    def _set_filter_style(self, f):
        self._filter = f
        for k, b in self._filter_btns.items():
            if k == f:
                b.config(bg=AMBER, fg="white")
            else:
                b.config(bg=WHITE, fg=TEXT_MUTE,
                         highlightbackground=CREAM, highlightthickness=1)

    def _set_filter(self, f):
        self._set_filter_style(f)
        self.load()

    def load(self):
        for w in self._tx_inner.winfo_children():
            w.destroy()
        org_id = self.org["id"]
        try:
            wres = supabase.table("wallets").select("id") \
                           .eq("organization_id", org_id).execute()
            wids = [w["id"] for w in (wres.data or [])]
            if not wids:
                tk.Label(self._tx_inner, text="No wallets found.",
                         bg=WHITE, fg=TEXT_MUTE,
                         font=("Poppins", 10)).pack(pady=40)
                return

            tres = supabase.table("wallet_transactions") \
                           .select("kind,date_issued,quantity,price,description,particulars,income_type") \
                           .in_("wallet_id", wids) \
                           .order("date_issued", desc=True).execute()
            txs = []
            for tx in (tres.data or []):
                d = tx.get("date_issued", "")[:10]
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d")
                    if dt.year != self._year or dt.month != self._month:
                        continue
                except Exception:
                    continue
                if self._filter != "all" and tx.get("kind") != self._filter:
                    continue
                txs.append(tx)

            if not txs:
                tk.Label(self._tx_inner,
                         text="No transactions for this period.",
                         bg=WHITE, fg=TEXT_MUTE,
                         font=("Poppins", 10)).pack(pady=40)
                return

            for tx in txs:
                kind  = tx.get("kind", "")
                qty   = int(tx.get("quantity") or 0)
                price = float(tx.get("price") or 0)
                amt   = qty * price
                color = GREEN_OK if kind == "income" else RED_ERR
                sign  = "+" if kind == "income" else "-"

                card = tk.Frame(self._tx_inner, bg=WHITE,
                                highlightbackground=CREAM, highlightthickness=1)
                card.pack(fill="x", pady=4, padx=2)

                left = tk.Frame(card, bg=WHITE)
                left.pack(side="left", fill="both", expand=True, padx=12, pady=8)
                desc = tx.get("description") or tx.get("particulars", "")
                tk.Label(left, text=desc[:40], bg=WHITE, fg=TEXT_DARK,
                         font=("Poppins", 10, "bold"), anchor="w").pack(anchor="w")
                sub = tx.get("income_type", "") or kind.capitalize()
                tk.Label(left, text=sub, bg=WHITE, fg=TEXT_MUTE,
                         font=("Poppins", 9), anchor="w").pack(anchor="w")
                tk.Label(left, text=tx.get("date_issued", "")[:10],
                         bg=WHITE, fg="#999999",
                         font=("Poppins", 8), anchor="w").pack(anchor="w")

                tk.Label(card, text=f"{sign}Php {amt:,.2f}",
                         bg=WHITE, fg=color, font=("Poppins", 11, "bold"),
                         padx=12).pack(side="right", pady=8)

        except Exception as e:
            messagebox.showerror("History Error", str(e))