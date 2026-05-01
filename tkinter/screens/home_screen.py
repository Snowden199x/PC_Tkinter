import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from constants import (
    WHITE, CREAM, AMBER, AMBER_MID, AMBER_LIGHT,
    CARD_GLASS, TEXT_DARK, TEXT_MUTE, TEXT_GRAY,
    ACTIVE_NAV, GREEN_OK, RED_ERR,
    supabase,
)

# Extra colours from web CSS not already in constants
BORDER_LIGHT  = "#F0E6D5"   # .wallet-card border
PROGRESS_BG   = "#F1F1F1"   # .progress-bar background
INCOME_ORANGE = "#C27A23"   # .income-stat
EXPENSE_AMBER = "#D18330"   # .expense-stat
DATE_GRAY     = "#999999"   # .transaction-date


class HomeTab(tk.Frame):
    """Dashboard home — pixel-faithful Tkinter port of pres_homepage."""

    def __init__(self, parent, org, supabase_client):
        super().__init__(parent, bg=WHITE)
        self.org      = org
        self.supabase = supabase_client
        self._build()
        self.load()

    # ══════════════════════════════════════════════════════
    # BUILD  (mirrors HTML structure top-to-bottom)
    # ══════════════════════════════════════════════════════
    def _build(self):
        # ── .header ──────────────────────────────────────
        hdr = tk.Frame(self, bg=WHITE)
        hdr.pack(fill="x", padx=40, pady=(28, 0))

        org_name = self.org.get("org_name", "")
        now      = datetime.now()

        # <h3>Hello, {org_name}</h3>  Playfair italic → Georgia italic
        tk.Label(
            hdr,
            text=f"Hello, {org_name}",
            bg=WHITE, fg=TEXT_DARK,
            font=("Georgia", 28, "italic"),
            anchor="w",
        ).pack(anchor="w")

        # <p class="date-text">
        tk.Label(
            hdr,
            text=now.strftime("%A, %B %d"),
            bg=WHITE, fg=TEXT_MUTE,
            font=("Poppins", 11, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # ── .summary-wrapper (amber gradient bar) ─────────
        self._build_summary_wrapper()

        # ── .overview (two columns) ───────────────────────
        self._build_overview()

        # ── Refresh button bottom-right ───────────────────
        refresh_row = tk.Frame(self, bg=WHITE)
        refresh_row.pack(fill="x", padx=40, pady=(8, 16))
        tk.Button(
            refresh_row,
            text="↻  Refresh",
            command=self.load,
            bg=AMBER, fg=WHITE,
            font=("Poppins", 9),
            relief="flat", cursor="hand2",
            activebackground=ACTIVE_NAV, activeforeground=WHITE,
            padx=16, pady=5,
        ).pack(side="right")

    # ──────────────────────────────────────────────────────
    # .summary-wrapper  — amber gradient bar + 4 glass cards
    # CSS: background: linear-gradient(90deg,#F3D58D,#ECB95D,#E59E2C)
    #      border-radius:25px  padding:20-25px
    # ──────────────────────────────────────────────────────
    def _build_summary_wrapper(self):
        wrapper = tk.Frame(
            self, bg=AMBER_MID,
            highlightbackground=AMBER_LIGHT,
            highlightthickness=0,
        )
        wrapper.pack(fill="x", padx=40, pady=(20, 0))

        inner = tk.Frame(wrapper, bg=AMBER_MID)
        inner.pack(fill="x", padx=20, pady=16)

        self._card_vars = {}
        cards = [
            ("total_balance",     "Total Balance",         "Php 0.00"),
            ("income_month",      "Income this month",     "Php 0.00"),
            ("expenses_month",    "Expenses this month",   "Php 0.00"),
            ("reports_submitted", "Reports submitted",     "0"),
        ]

        for key, label, default in cards:
            # .summary .card — rgba(255,255,255,0.4), border-radius:15px
            card = tk.Frame(
                inner, bg=CARD_GLASS,
                highlightbackground="#E8C97A",
                highlightthickness=1,
            )
            card.pack(side="left", fill="both", expand=True, padx=8, pady=2)

            # <p> font-size:12-13px, font-weight:500
            tk.Label(
                card, text=label,
                bg=CARD_GLASS, fg=TEXT_DARK,
                font=("Poppins", 9, "bold"),
                wraplength=140, justify="left",
                anchor="w",
            ).pack(anchor="w", padx=16, pady=(14, 2))

            # <h2> font-size:13-15px, font-weight:500
            var = tk.StringVar(value=default)
            self._card_vars[key] = var
            tk.Label(
                card, textvariable=var,
                bg=CARD_GLASS, fg=TEXT_DARK,
                font=("Poppins", 13, "bold"),
                anchor="w",
            ).pack(anchor="w", padx=16, pady=(0, 14))

    # ──────────────────────────────────────────────────────
    # .overview — two-column flex layout
    # CSS: display:flex; gap:40px; margin-top:40px
    # ──────────────────────────────────────────────────────
    def _build_overview(self):
        overview = tk.Frame(self, bg=WHITE)
        overview.pack(fill="both", expand=True, padx=40, pady=(28, 0))

        # Left: .wallets
        left_col = tk.Frame(overview, bg=WHITE)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # <h4> font-weight:500, font-size:~20px
        tk.Label(
            left_col, text="Wallets Overview",
            bg=WHITE, fg=TEXT_DARK,
            font=("Poppins", 14, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        # .overview-box — white, border-radius:20px, max-height:280px scrollable
        self._wallets_box, self._wallets_inner = self._overview_box(left_col)

        # Right: .transactions
        right_col = tk.Frame(overview, bg=WHITE)
        right_col.pack(side="left", fill="both", expand=True, padx=(20, 0))

        tk.Label(
            right_col, text="Transaction History",
            bg=WHITE, fg=TEXT_DARK,
            font=("Poppins", 14, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        self._tx_box, self._tx_inner = self._overview_box(right_col)

    def _overview_box(self, parent):
        """
        .overview-box — white, rounded, subtle shadow, max-height 280 scrollable.
        Returns (outer_frame, inner_scrollable_frame).
        """
        outer = tk.Frame(
            parent, bg=WHITE,
            highlightbackground=BORDER_LIGHT,
            highlightthickness=1,
        )
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=WHITE, highlightthickness=0)
        sb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner  = tk.Frame(canvas, bg=WHITE)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _wheel)

        return outer, inner

    # ══════════════════════════════════════════════════════
    # LOAD DATA
    # ══════════════════════════════════════════════════════
    def load(self):
        org_id = self.org["id"]
        try:
            wres       = self.supabase.table("wallets") \
                                      .select("id,name") \
                                      .eq("organization_id", org_id).execute()
            wallets    = wres.data or []
            wallet_ids = [w["id"] for w in wallets]

            income_all = expense_all = income_mo = expense_mo = 0.0
            now          = datetime.now()
            txs_all      = []
            wallet_stats = {}

            if wallet_ids:
                tres = self.supabase.table("wallet_transactions") \
                                    .select("kind,date_issued,quantity,price,"
                                            "description,particulars,income_type,wallet_id") \
                                    .in_("wallet_id", wallet_ids).execute()

                for tx in (tres.data or []):
                    qty   = int(tx.get("quantity") or 0)
                    price = float(tx.get("price") or 0)
                    amt   = qty * price
                    wid   = tx.get("wallet_id")
                    kind  = tx.get("kind", "")

                    if wid not in wallet_stats:
                        wallet_stats[wid] = {"income": 0.0, "expense": 0.0, "budget": 0.0}

                    if kind == "income":
                        income_all += amt
                        wallet_stats[wid]["income"] += amt
                    else:
                        expense_all += amt
                        wallet_stats[wid]["expense"] += amt

                    d = tx.get("date_issued", "")[:10]
                    try:
                        dt = datetime.strptime(d, "%Y-%m-%d")
                        if dt.year == now.year and dt.month == now.month:
                            if kind == "income":
                                income_mo += amt
                            else:
                                expense_mo += amt
                    except Exception:
                        pass
                    txs_all.append(tx)

                bres = self.supabase.table("wallet_budgets") \
                                    .select("amount,wallet_id") \
                                    .in_("wallet_id", wallet_ids).execute()
                beginning = 0.0
                for b in (bres.data or []):
                    amt = float(b.get("amount") or 0)
                    beginning += amt
                    wid = b.get("wallet_id")
                    if wid in wallet_stats:
                        wallet_stats[wid]["budget"] += amt

                total_bal = beginning + income_all - expense_all
            else:
                total_bal = 0.0

            rres = self.supabase.table("financial_reports") \
                                .select("id", count="exact") \
                                .eq("organization_id", org_id) \
                                .in_("status", ["Submitted", "Approved"]).execute()
            reports = rres.count or 0

            self._card_vars["total_balance"].set(f"Php {total_bal:,.2f}")
            self._card_vars["income_month"].set(f"Php {income_mo:,.2f}")
            self._card_vars["expenses_month"].set(f"Php {expense_mo:,.2f}")
            self._card_vars["reports_submitted"].set(str(reports))

            self._render_wallets(wallets, wallet_stats)
            self._render_transactions(txs_all)

        except Exception as e:
            messagebox.showerror("Dashboard Error", str(e))

    # ══════════════════════════════════════════════════════
    # RENDER WALLETS  (.wallet-card)
    # ══════════════════════════════════════════════════════
    def _render_wallets(self, wallets, wallet_stats):
        for w in self._wallets_inner.winfo_children():
            w.destroy()

        if not wallets:
            self._empty_card(self._wallets_inner,
                             "No wallets yet",
                             "Create your first wallet to start tracking.")
            return

        for wallet in wallets[:6]:
            wid    = wallet["id"]
            stats  = wallet_stats.get(wid, {"income": 0.0, "expense": 0.0, "budget": 0.0})
            budget = stats["budget"]
            inc    = stats["income"]
            exp    = stats["expense"]
            pct    = min(exp / budget, 1.0) if budget > 0 else 0.0

            # .wallet-card — white, border:#F0E6D5, border-radius:20px, padding:18 22
            card = tk.Frame(
                self._wallets_inner, bg=WHITE,
                highlightbackground=BORDER_LIGHT,
                highlightthickness=1,
            )
            card.pack(fill="x", padx=10, pady=6)

            # .wallet-details
            details = tk.Frame(card, bg=WHITE)
            details.pack(fill="x", padx=18, pady=(12, 4))

            # <h5> font-weight:600, font-size:15px
            tk.Label(
                details,
                text=wallet.get("name", ""),
                bg=WHITE, fg=TEXT_DARK,
                font=("Poppins", 11, "bold"),
                anchor="w",
            ).pack(anchor="w")

            # .budget-text  font-size:12px, color:#777
            tk.Label(
                details, text="Budget used",
                bg=WHITE, fg=TEXT_GRAY,
                font=("Poppins", 8),
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

            # .budget-amount  right-aligned, font-size:13px
            tk.Label(
                details,
                text=f"Php {exp:,.2f} / Php {budget:,.2f}",
                bg=WHITE, fg=TEXT_DARK,
                font=("Poppins", 9, "bold"),
                anchor="e",
            ).pack(fill="x")

            # .progress-bar  h:8px, bg:#F1F1F1, border-radius:999px
            prog_bg = tk.Frame(details, bg=PROGRESS_BG, height=8)
            prog_bg.pack(fill="x", pady=(6, 4))
            prog_bg.pack_propagate(False)
            if pct > 0:
                # .progress-fill  bg:#A25517
                fill = tk.Frame(prog_bg, bg="#A25517", height=8)
                fill.place(relx=0, rely=0, relwidth=pct, relheight=1.0)

            # .wallet-stats  — income left, expense right
            stats_row = tk.Frame(card, bg=WHITE)
            stats_row.pack(fill="x", padx=18, pady=(0, 12))

            # .income-stat  color:#C27A23
            tk.Label(
                stats_row,
                text=f"+Php {inc:,.2f}",
                bg=WHITE, fg=INCOME_ORANGE,
                font=("Poppins", 9, "bold"),
            ).pack(side="left")

            # .expense-stat  color:#D18330
            tk.Label(
                stats_row,
                text=f"-Php {exp:,.2f}",
                bg=WHITE, fg=EXPENSE_AMBER,
                font=("Poppins", 9, "bold"),
            ).pack(side="right")

    # ══════════════════════════════════════════════════════
    # RENDER TRANSACTIONS  (.transaction-item)
    # ══════════════════════════════════════════════════════
    def _render_transactions(self, txs_all):
        for w in self._tx_inner.winfo_children():
            w.destroy()

        recent = sorted(
            txs_all,
            key=lambda x: x.get("date_issued", ""),
            reverse=True,
        )[:8]

        if not recent:
            self._empty_card(self._tx_inner,
                             "No transactions yet",
                             "Your history will appear once you add entries.")
            return

        for tx in recent:
            qty   = int(tx.get("quantity") or 0)
            price = float(tx.get("price") or 0)
            amt   = qty * price
            kind  = tx.get("kind", "")
            # .transaction-amount.income → GREEN_OK / .expense → RED_ERR
            color = GREEN_OK if kind == "income" else RED_ERR
            sign  = "+" if kind == "income" else "-"
            desc  = tx.get("description") or tx.get("particulars", "—")
            sub   = tx.get("income_type", "") or kind.capitalize()
            date  = tx.get("date_issued", "")[:10]

            # .transaction-item — white, border:#ECDDC6, border-radius:12px, padding:15px
            item = tk.Frame(
                self._tx_inner, bg=WHITE,
                highlightbackground=CREAM,
                highlightthickness=1,
            )
            item.pack(fill="x", padx=10, pady=5)

            # .transaction-info (left)
            info = tk.Frame(item, bg=WHITE)
            info.pack(side="left", fill="both", expand=True, padx=14, pady=12)

            # <h5> font-weight:600, font-size:14px
            tk.Label(
                info, text=desc[:42],
                bg=WHITE, fg=TEXT_DARK,
                font=("Poppins", 10, "bold"),
                anchor="w",
            ).pack(anchor="w")

            # <p> font-size:12px, color:#616161
            tk.Label(
                info, text=sub,
                bg=WHITE, fg=TEXT_MUTE,
                font=("Poppins", 8),
                anchor="w",
            ).pack(anchor="w")

            # .transaction-date  font-size:11px, color:#999
            tk.Label(
                info, text=date,
                bg=WHITE, fg=DATE_GRAY,
                font=("Poppins", 8),
                anchor="w",
            ).pack(anchor="w")

            # .transaction-amount  font-weight:600, font-size:16px
            tk.Label(
                item,
                text=f"{sign}Php {amt:,.2f}",
                bg=WHITE, fg=color,
                font=("Poppins", 11, "bold"),
                padx=14,
            ).pack(side="right", pady=12)

    # ══════════════════════════════════════════════════════
    # EMPTY STATE  (.empty-card)
    # CSS: white, border:#ECDDC6, border-radius:15px, text-align:center
    # ══════════════════════════════════════════════════════
    def _empty_card(self, parent, title, subtitle):
        card = tk.Frame(
            parent, bg=WHITE,
            highlightbackground=CREAM,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(card, text="—", bg=WHITE, fg=CREAM,
                 font=("Poppins", 28, "bold")).pack(pady=(30, 4))
        tk.Label(card, text=title, bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 11, "bold")).pack()
        tk.Label(card, text=subtitle, bg=WHITE, fg=TEXT_MUTE,
                 font=("Poppins", 9), wraplength=260,
                 justify="center").pack(pady=(4, 31))