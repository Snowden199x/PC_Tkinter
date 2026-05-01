import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
from constants import *
from datetime import datetime
from PIL import Image, ImageTk
from db import (get_wallets, get_wallet_transactions,
                get_wallet_receipts, get_wallet_reports, get_wallet_budget)

_ASSETS      = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "assets", "images")
_CARD_COLORS = ["#F3D58D","#D4E8C2","#C2D4E8","#E8C2D4","#D4C2E8","#C2E8D4","#E8D4C2"]
_INCOME_CLR  = "#2E7D32"
_EXPENSE_CLR = "#C62828"
_ACTIVE_TAB  = "#E59E2C"
_FILTER_ACT  = "#E59E2C"
_FILTER_BDR  = "#ECDDC6"
_BTN_BROWN   = "#A24A00"
_BTN_HOV     = "#8B3A00"


def _img(name, w, h, cache):
    path = _os.path.join(_ASSETS, name)
    if not _os.path.exists(path):
        return None
    try:
        ph = ImageTk.PhotoImage(Image.open(path).resize((w, h), Image.LANCZOS))
        cache.append(ph)
        return ph
    except Exception:
        return None


class WalletScreen(tk.Frame):
    def __init__(self, parent, org=None, **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._org   = org or {}
        self._imgs  = []
        self._view  = "list"          # "list" | "detail"
        self._wallet = None           # selected wallet dict
        self._build()

    # ── outer scaffold ────────────────────────────────────────────────
    def _build(self):
        outer = tk.Frame(self, bg=BG_CREAM, padx=20, pady=16)
        outer.pack(fill="both", expand=True)
        self._box = tk.Frame(outer, bg=BG_WHITE, padx=36, pady=28)
        self._box.pack(fill="both", expand=True)
        self._show_list_view()

    # ══════════════════════════════════════════════════════════════════
    # LIST VIEW
    # ══════════════════════════════════════════════════════════════════
    def _show_list_view(self):
        self._clear_box()
        self._view = "list"

        # ── header row ────────────────────────────────────────────────
        hdr = tk.Frame(self._box, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="Wallets", bg=BG_WHITE, fg=TEXT_DARK,
                 font=("Georgia", 22, "italic")).pack(side="left")

        # academic year dropdown
        self._year_var = tk.StringVar(value="All years")
        self._year_menu = ttk.Combobox(hdr, textvariable=self._year_var,
                                       state="readonly", width=12,
                                       font=font(9))
        self._year_menu.pack(side="right", padx=(6, 0))

        # search bar
        self._search_var = tk.StringVar()
        search = tk.Entry(hdr, textvariable=self._search_var,
                          font=font(9), bd=1, relief="solid",
                          highlightbackground=_FILTER_BDR,
                          highlightthickness=1)
        search.insert(0, "Search wallet...")
        search.config(fg=TEXT_MUTED)
        search.pack(side="right", ipady=5, ipadx=8)

        def _focus_in(e):
            if search.get() == "Search wallet...":
                search.delete(0, "end")
                search.config(fg=TEXT_DARK)
        def _focus_out(e):
            if not search.get():
                search.insert(0, "Search wallet...")
                search.config(fg=TEXT_MUTED)
        search.bind("<FocusIn>",  _focus_in)
        search.bind("<FocusOut>", _focus_out)

        # loading
        loading = tk.Label(self._box, text="Loading wallets...",
                           bg=BG_WHITE, fg=TEXT_MUTED, font=font(10))
        loading.pack(pady=30)
        self.update()

        try:
            all_wallets = get_wallets(self._org.get("id"))
        except Exception:
            all_wallets = []
        loading.destroy()

        if not all_wallets:
            self._empty(self._box, "No wallets found.",
                        "No active wallets for this organization.")
            return

        # build academic year list
        acad_years = sorted(set(w["acad_year"] for w in all_wallets), reverse=True)
        self._year_menu["values"] = ["All years"] + acad_years

        # default to current academic year
        now = datetime.now()
        cur_ay = (f"{now.year}-{now.year+1}" if now.month >= 8
                  else f"{now.year-1}-{now.year}")
        if cur_ay in acad_years:
            self._year_var.set(cur_ay)
        else:
            self._year_var.set(acad_years[0] if acad_years else "All years")

        # scrollable area
        canvas = tk.Canvas(self._box, bg=BG_WHITE, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(self._box, orient="vertical", command=canvas.yview)
        self._grid_inner = tk.Frame(canvas, bg=BG_WHITE)
        self._grid_inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._canvas_win = canvas.create_window((0, 0), window=self._grid_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        # keep inner frame same width as canvas
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self._canvas_win, width=e.width))
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._bind_scroll(canvas)

        self._all_wallets  = all_wallets
        self._wallet_cards = []
        wallet_img = _img("wallet.png", 160, 150, self._imgs)
        self._wallet_img   = wallet_img

        # wire up filters — rebuild grid on change
        self._search_var.trace_add("write", lambda *_: self._apply_filters())
        self._year_var.trace_add("write",   lambda *_: self._apply_filters())

        # initial render
        self._apply_filters()

    def _apply_filters(self):
        q  = self._search_var.get().lower()
        if q == "search wallet...":
            q = ""
        ay = self._year_var.get()

        # destroy all existing cards and rows
        for w in self._grid_inner.winfo_children():
            w.destroy()
        self._wallet_cards = []

        visible = [
            w for w in self._all_wallets
            if (q in w["name"].lower() or q in w["month"].lower())
            and (ay == "All years" or w["acad_year"] == ay)
        ]

        if not visible:
            tk.Label(self._grid_inner, text="No wallets match.",
                     bg=BG_WHITE, fg=TEXT_MUTED, font=font(9)).pack(pady=20)
            return

        cols = 4
        row_f = None
        for i, w in enumerate(visible):
            if i % cols == 0:
                row_f = tk.Frame(self._grid_inner, bg=BG_WHITE)
                row_f.pack(anchor="w", pady=(0, 8))
            color = _CARD_COLORS[i % len(_CARD_COLORS)]
            card = self._wallet_card(row_f, w, color, self._wallet_img)
            self._wallet_cards.append((card, w))

    def _wallet_card(self, parent, w, color, wallet_img):
        CARD_W, CARD_H = 160, 150

        outer = tk.Frame(parent, bg=BG_WHITE, cursor="hand2")
        outer.pack(side="left", padx=(0, 8))

        cv = tk.Canvas(outer, width=CARD_W, height=CARD_H,
                       bd=0, highlightthickness=2,
                       highlightbackground="#ddd", bg=color)
        cv.pack()

        if wallet_img:
            cv.create_image(0, 0, image=wallet_img, anchor="nw")

        month_name = w.get("month_name", "").upper()
        pad_x, pad_y = 6, 3
        text_w = len(month_name) * 7 + pad_x * 2
        text_h = 16 + pad_y * 2
        x1, y1 = 8, CARD_H - 10 - text_h
        x2, y2 = x1 + text_w, CARD_H - 10
        cv.create_rectangle(x1, y1, x2, y2, fill="white", outline="", width=0)
        cv.create_text(x1 + pad_x, (y1 + y2) // 2,
                       text=month_name, anchor="w",
                       font=font(8, "bold"), fill=TEXT_DARK)

        def _enter(e): cv.config(highlightbackground=_BTN_BROWN, highlightthickness=2)
        def _leave(e): cv.config(highlightbackground="#ddd", highlightthickness=1)
        def _click(e, wallet=w): self._show_detail_view(wallet)

        for widget in (outer, cv):
            widget.bind("<Button-1>", _click)
            widget.bind("<Enter>",    _enter)
            widget.bind("<Leave>",    _leave)

        outer._wallet_name = w["name"]
        return outer

    # ══════════════════════════════════════════════════════════════════
    # DETAIL VIEW
    # ══════════════════════════════════════════════════════════════════
    def _show_detail_view(self, wallet):
        self._clear_box()
        self._view      = "detail"
        self._wallet    = wallet
        self._tx_filter = "all"

        # ── header ────────────────────────────────────────────────────
        hdr = tk.Frame(self._box, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 4))

        # back
        back = tk.Label(hdr, text="‹", bg=BG_WHITE, fg=_BTN_BROWN,
                        font=font(22), cursor="hand2")
        back.pack(side="left")
        back.bind("<Button-1>", lambda e: self._show_list_view())
        back.bind("<Enter>",    lambda e: back.config(fg="#5A2D0C"))
        back.bind("<Leave>",    lambda e: back.config(fg=_BTN_BROWN))

        # title — month name only, italic Georgia
        month_title = wallet.get("month_name", "").capitalize()
        tk.Label(hdr, text=month_title, bg=BG_WHITE, fg=TEXT_DARK,
                 font=("Georgia", 16, "italic")).pack(side="left", padx=(8, 0))

        # —— Add budget secondary button (right side) ——
        budget_btn = tk.Label(hdr, text="Add budget for this month",
                              bg=BG_WHITE, fg="#616161",
                              font=font(8), padx=12, pady=7,
                              cursor="hand2",
                              highlightbackground=_FILTER_BDR,
                              highlightthickness=1)
        budget_btn.pack(side="right", padx=(6, 0))
        budget_btn.bind("<Enter>", lambda e: budget_btn.config(bg="#F5F1E8"))
        budget_btn.bind("<Leave>", lambda e: budget_btn.config(bg=BG_WHITE))

        # —— + Add button with dropdown ——
        add_wrap = tk.Frame(hdr, bg=BG_WHITE)
        add_wrap.pack(side="right", padx=(0, 6))

        add_btn = tk.Label(add_wrap, text="+ Add", bg=_BTN_BROWN, fg="white",
                           font=font(9, "bold"), padx=14, pady=7, cursor="hand2")
        add_btn.pack()
        add_btn.bind("<Enter>", lambda e: add_btn.config(bg=_BTN_HOV))
        add_btn.bind("<Leave>", lambda e: add_btn.config(bg=_BTN_BROWN))

        # dropdown
        drop = tk.Frame(self._box, bg="white",
                        highlightbackground="#ddd", highlightthickness=1)
        drop._open = False

        for txt, kind in [("Add income transaction", "income"),
                          ("Add expense transaction", "expense")]:
            item = tk.Label(drop, text=txt, bg="white", fg=TEXT_DARK,
                            font=font(9), padx=16, pady=8, anchor="w",
                            cursor="hand2")
            item.pack(fill="x")
            item.bind("<Enter>", lambda e, b=item: b.config(bg="#F5F1E8"))
            item.bind("<Leave>", lambda e, b=item: b.config(bg="white"))
            item.bind("<Button-1>",
                      lambda e, k=kind: (self._close_drop(drop),
                                         self._open_tx_dialog(k)))

        def _toggle(e=None):
            if drop._open:
                self._close_drop(drop)
            else:
                drop.place(in_=self._box, relx=1.0, rely=0,
                           anchor="ne", x=-36, y=60)
                drop.lift()
                drop._open = True

        add_btn.bind("<Button-1>", _toggle)

        # ── tab nav ───────────────────────────────────────────────────
        tab_bar = tk.Frame(self._box, bg=BG_WHITE,
                           highlightbackground=_FILTER_BDR,
                           highlightthickness=0)
        tab_bar.pack(fill="x", pady=(12, 0))

        # bottom border line
        tk.Frame(self._box, bg=_FILTER_BDR, height=2).pack(fill="x")

        self._tab_btns = {}
        self._tab_content = tk.Frame(self._box, bg=BG_WHITE)
        self._tab_content.pack(fill="both", expand=True, pady=(12, 0))

        for key, label in [("transactions","Transactions"),("reports","Reports"),
                            ("receipts","Receipts"),("archives","Archive")]:
            btn = tk.Label(tab_bar, text=label, bg=BG_WHITE, fg="#616161",
                           font=font(10, "bold"), padx=20, pady=10,
                           cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            btn.bind("<Enter>",    lambda e, b=btn, k=key: b.config(fg=TEXT_DARK) if k != self._active_tab else None)
            btn.bind("<Leave>",    lambda e, b=btn, k=key: b.config(fg="#616161") if k != self._active_tab else None)
            self._tab_btns[key] = btn

        self._active_tab = "transactions"
        self._switch_tab("transactions")

    def _close_drop(self, drop):
        drop.place_forget()
        drop._open = False

    def _open_tx_dialog(self, kind):
        """Placeholder — shows a simple info label for now."""
        import tkinter.messagebox as mb
        mb.showinfo("Add Transaction",
                    f"Add {kind} transaction for {self._wallet.get('month_name','')}")

    def _switch_tab(self, key):
        self._active_tab = key
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.config(fg=TEXT_DARK, font=font(10, "bold"))
                # underline effect via a small frame below
            else:
                btn.config(fg="#616161", font=font(10))

        for w in self._tab_content.winfo_children():
            w.destroy()

        if key == "transactions":
            self._tab_transactions()
        elif key == "reports":
            self._tab_reports()
        elif key == "receipts":
            self._tab_receipts()
        elif key == "archives":
            self._tab_archives()

    # ── TRANSACTIONS TAB ──────────────────────────────────────────────
    def _tab_transactions(self):
        p = self._tab_content

        # filter tabs
        flt_row = tk.Frame(p, bg=BG_WHITE)
        flt_row.pack(pady=(0, 12))
        self._flt_btns = {}
        for key, lbl in [("all","All"),("income","Income"),("expense","Expense")]:
            b = tk.Label(flt_row, text=lbl, bg=BG_WHITE, fg=TEXT_DARK,
                         font=font(9), padx=22, pady=7, cursor="hand2",
                         highlightbackground=_FILTER_BDR, highlightthickness=2)
            b.pack(side="left", padx=5)
            b.bind("<Button-1>", lambda e, k=key: self._set_tx_filter(k))
            self._flt_btns[key] = b
        self._set_tx_filter(self._tx_filter, refresh=False)
        self._update_flt_styles()

        # list area
        self._tx_list = tk.Frame(p, bg=BG_WHITE)
        self._tx_list.pack(fill="both", expand=True)
        self._load_transactions()

    def _set_tx_filter(self, key, refresh=True):
        self._tx_filter = key
        self._update_flt_styles()
        if refresh:
            self._load_transactions()

    def _update_flt_styles(self):
        for k, b in self._flt_btns.items():
            if k == self._tx_filter:
                b.config(bg=_FILTER_ACT, fg="white", highlightbackground=_FILTER_ACT)
            else:
                b.config(bg=BG_WHITE, fg=TEXT_DARK, highlightbackground=_FILTER_BDR)

    def _load_transactions(self):
        for w in self._tx_list.winfo_children():
            w.destroy()

        loading = tk.Label(self._tx_list, text="Loading...",
                           bg=BG_WHITE, fg=TEXT_MUTED, font=font(9))
        loading.pack(pady=10)
        self.update()

        try:
            rows = get_wallet_transactions(self._wallet["id"], self._tx_filter,
                                           year=self._wallet.get("year"),
                                           month=self._wallet.get("month_id"))
        except Exception:
            rows = []
        loading.destroy()

        canvas = tk.Canvas(self._tx_list, bg=BG_WHITE, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(self._tx_list, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_WHITE)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._bind_scroll(canvas)

        if not rows:
            self._empty(inner, "No transactions found.", "Try a different filter.")
            return

        for t in rows:
            self._tx_item(inner, t)

    def _tx_item(self, parent, t):
        date  = t.get("date_issued", "")[:10]
        desc  = t.get("description") or t.get("particulars") or "—"
        cat   = t.get("income_type") or t.get("particulars") or t["kind"].capitalize()
        amt   = t["price"] * t["quantity"]
        if t["kind"] == "expense":
            amt = -amt

        card = tk.Frame(parent, bg=BG_WHITE,
                        highlightbackground=_FILTER_BDR,
                        highlightthickness=1, padx=14, pady=10)
        card.pack(fill="x", pady=4, padx=2)
        card.bind("<Enter>", lambda e: card.config(highlightbackground=_ACTIVE_TAB))
        card.bind("<Leave>", lambda e: card.config(highlightbackground=_FILTER_BDR))

        left = tk.Frame(card, bg=BG_WHITE)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=desc, bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(9, "bold"), anchor="w").pack(anchor="w")
        tk.Label(left, text=cat,  bg=BG_WHITE, fg=TEXT_MUTED,
                 font=font(8), anchor="w").pack(anchor="w")
        tk.Label(left, text=date, bg=BG_WHITE, fg="#999999",
                 font=font(7), anchor="w").pack(anchor="w")

        color = _INCOME_CLR if amt >= 0 else _EXPENSE_CLR
        sign  = "+" if amt >= 0 else "-"
        tk.Label(card, text=f"{sign}₱{abs(amt):,.2f}",
                 bg=BG_WHITE, fg=color,
                 font=font(10, "bold")).pack(side="right", anchor="center")

    # ── REPORTS TAB ───────────────────────────────────────────────────
    def _tab_reports(self):
        p = self._tab_content

        try:
            budget  = get_wallet_budget(self._wallet["id"],
                                        self._wallet.get("year"),
                                        self._wallet.get("month_id"))
            txs     = get_wallet_transactions(self._wallet["id"],
                                              year=self._wallet.get("year"),
                                              month=self._wallet.get("month_id"))
            income  = sum(t["price"]*t["quantity"] for t in txs if t["kind"]=="income")
            expense = sum(t["price"]*t["quantity"] for t in txs if t["kind"]=="expense")
            ending  = income - expense
        except Exception:
            budget = income = expense = ending = 0.0

        # amber gradient report header
        banner = tk.Frame(p, bg="#E59E2C", padx=20, pady=18)
        banner.pack(fill="x", pady=(0, 16))

        reports_img = _img("reports.png", 44, 44, self._imgs)
        if reports_img:
            tk.Label(banner, image=reports_img, bg="#E59E2C").pack(side="left", padx=(0, 14))

        info = tk.Frame(banner, bg="#E59E2C")
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text="Generate Financial Report", bg="#E59E2C",
                 fg=TEXT_DARK, font=font(11, "bold")).pack(anchor="w")
        tk.Label(info, text="Create an Activity Financial Statement for this wallet.",
                 bg="#E59E2C", fg="#616161", font=font(8)).pack(anchor="w")

        gen_btn = tk.Label(banner, text="Generate report", bg=BG_WHITE,
                           fg=TEXT_DARK, font=font(9, "bold"),
                           padx=14, pady=8, cursor="hand2")
        gen_btn.pack(side="right")
        gen_btn.bind("<Enter>", lambda e: gen_btn.config(bg=_FILTER_BDR))
        gen_btn.bind("<Leave>", lambda e: gen_btn.config(bg=BG_WHITE))

        # stat cards
        stats_row = tk.Frame(p, bg=BG_WHITE)
        stats_row.pack(fill="x")
        for i, (lbl, val) in enumerate([
            ("Budget",                  f"₱{budget:,.2f}"),
            ("Total amount of income",  f"₱{income:,.2f}"),
            ("Total amount of expenses",f"₱{expense:,.2f}"),
            ("Ending Cash",             f"₱{ending:,.2f}"),
        ]):
            stats_row.columnconfigure(i, weight=1)
            card = tk.Frame(stats_row, bg=BG_WHITE,
                            highlightbackground=_FILTER_BDR,
                            highlightthickness=2, padx=14, pady=14)
            card.grid(row=0, column=i, padx=6, sticky="nsew")
            tk.Label(card, text=lbl, bg=BG_WHITE, fg="#616161",
                     font=font(7), wraplength=130, justify="center").pack()
            tk.Label(card, text=val, bg=BG_WHITE, fg=TEXT_DARK,
                     font=font(10, "bold")).pack(pady=(6, 0))

    # ── RECEIPTS TAB ──────────────────────────────────────────────────
    def _tab_receipts(self):
        p = self._tab_content
        loading = tk.Label(p, text="Loading receipts...",
                           bg=BG_WHITE, fg=TEXT_MUTED, font=font(9))
        loading.pack(pady=10)
        self.update()

        try:
            receipts = get_wallet_receipts(self._wallet["id"])
        except Exception:
            receipts = []
        loading.destroy()

        if not receipts:
            self._empty(p, "No receipts found.", "No receipts uploaded for this wallet.")
            return

        canvas = tk.Canvas(p, bg=BG_WHITE, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(p, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_WHITE)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._bind_scroll(canvas)

        receipts_ico = _img("receipts.png", 36, 36, self._imgs)
        cols = 4
        for i, r in enumerate(receipts):
            col_i = i % cols
            row_i = i // cols
            inner.columnconfigure(col_i, weight=1)
            self._receipt_card(inner, row_i, col_i, r, receipts_ico)

    def _receipt_card(self, parent, row, col, r, icon):
        card = tk.Frame(parent, bg=BG_WHITE,
                        highlightbackground=_FILTER_BDR,
                        highlightthickness=2, padx=14, pady=14)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        ico_frm = tk.Frame(card, bg="#F5F5F5", width=60, height=60)
        ico_frm.pack(pady=(0, 8))
        ico_frm.pack_propagate(False)
        if icon:
            tk.Label(ico_frm, image=icon, bg="#F5F5F5").place(relx=0.5, rely=0.5, anchor="center")

        desc = r.get("description") or "Receipt"
        date = r.get("receipt_date", "")[:10]
        tk.Label(card, text=desc, bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(8, "bold"), wraplength=130).pack()
        tk.Label(card, text=date, bg=BG_WHITE, fg=TEXT_MUTED,
                 font=font(7)).pack(pady=(2, 8))

        view_btn = tk.Label(card, text="View", bg=_FILTER_BDR,
                            fg=TEXT_DARK, font=font(8, "bold"),
                            padx=10, pady=4, cursor="hand2")
        view_btn.pack()
        view_btn.bind("<Enter>", lambda e: view_btn.config(bg="#D4C4A8"))
        view_btn.bind("<Leave>", lambda e: view_btn.config(bg=_FILTER_BDR))

    # ── ARCHIVES TAB ──────────────────────────────────────────────────
    def _tab_archives(self):
        p = self._tab_content
        loading = tk.Label(p, text="Loading reports...",
                           bg=BG_WHITE, fg=TEXT_MUTED, font=font(9))
        loading.pack(pady=10)
        self.update()

        try:
            reports = get_wallet_reports(self._org.get("id"), self._wallet["id"])
        except Exception:
            reports = []
        loading.destroy()

        if not reports:
            self._empty(p, "No archived reports.", "No financial reports submitted yet.")
            return

        canvas = tk.Canvas(p, bg=BG_WHITE, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(p, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_WHITE)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._bind_scroll(canvas)

        cols = 3
        for i, rep in enumerate(reports):
            col_i = i % cols
            row_i = i // cols
            inner.columnconfigure(col_i, weight=1)
            self._archive_card(inner, row_i, col_i, rep)

    def _archive_card(self, parent, row, col, rep):
        card = tk.Frame(parent, bg=BG_WHITE,
                        highlightbackground=_FILTER_BDR,
                        highlightthickness=2, padx=16, pady=14)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        rep_no = rep.get("report_no") or f"FR-{rep['id']:03d}"
        tk.Label(card, text=rep_no, bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(10, "bold")).pack()

        event = rep.get("event_name") or "—"
        date  = (rep.get("submission_date") or "")[:10]
        status = rep.get("status") or "—"
        income  = rep.get("total_income")  or 0
        expense = rep.get("total_expense") or 0
        ending  = (income or 0) - (expense or 0)

        for lbl, val in [("Event", event), ("Date", date), ("Status", status),
                         ("Income", f"₱{income:,.2f}"),
                         ("Expense", f"₱{expense:,.2f}"),
                         ("Ending Cash", f"₱{ending:,.2f}")]:
            row_f = tk.Frame(card, bg=BG_WHITE)
            row_f.pack(fill="x", pady=1)
            tk.Label(row_f, text=lbl+":", bg=BG_WHITE, fg=TEXT_MUTED,
                     font=font(7), anchor="w", width=10).pack(side="left")
            tk.Label(row_f, text=str(val), bg=BG_WHITE, fg=TEXT_DARK,
                     font=font(7, "bold"), anchor="w").pack(side="left")

        dl_btn = tk.Label(card, text="Download", bg=_BTN_BROWN,
                          fg="white", font=font(8, "bold"),
                          padx=10, pady=4, cursor="hand2")
        dl_btn.pack(pady=(8, 0))
        dl_btn.bind("<Enter>", lambda e: dl_btn.config(bg=_BTN_HOV))
        dl_btn.bind("<Leave>", lambda e: dl_btn.config(bg=_BTN_BROWN))

    # ── helpers ───────────────────────────────────────────────────────
    def _clear_box(self):
        for w in self._box.winfo_children():
            w.destroy()

    def _empty(self, parent, title, subtitle):
        frm = tk.Frame(parent, bg=BG_WHITE)
        frm.pack(expand=True, pady=40)
        tk.Label(frm, text=title, bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(11, "bold")).pack()
        tk.Label(frm, text=subtitle, bg=BG_WHITE, fg=TEXT_MUTED,
                 font=font(9)).pack(pady=(4, 0))

    def _bind_scroll(self, canvas):
        def _scroll(e):
            try:
                canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _scroll)
        canvas.bind("<Destroy>",
                    lambda e: canvas.unbind_all("<MouseWheel>")
                    if e.widget is canvas else None)
