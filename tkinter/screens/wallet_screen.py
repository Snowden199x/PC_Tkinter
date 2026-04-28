"""
wallet_screen.py — Wallets tab and Add Transaction dialog.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from constants import (
    WHITE, CREAM, AMBER, AMBER_LIGHT,
    TEXT_DARK, TEXT_MUTE, ACTIVE_NAV, GREEN_OK, RED_ERR,
    styled_btn, supabase
)


# ═══════════════════════════════════════════════════════════
# WALLETS TAB
# ═══════════════════════════════════════════════════════════
class WalletsTab(tk.Frame):
    def __init__(self, parent, org):
        super().__init__(parent, bg=WHITE)
        self.org          = org
        self._folders     = []
        self._sel_folder  = None
        self._tx_filter   = "all"
        self._build()
        self._show_list()
        self.load_folders()

    def _build(self):
        # ── LIST VIEW ──────────────────────────────────────
        self._list_view = tk.Frame(self, bg=WHITE)

        lhdr = tk.Frame(self._list_view, bg=WHITE)
        lhdr.pack(fill="x", padx=30, pady=(24, 0))
        tk.Label(lhdr, text="Wallets", bg=WHITE, fg=TEXT_DARK,
                 font=("Georgia", 22, "italic")).pack(side="left")
        styled_btn(lhdr, "↻ Refresh", self.load_folders,
                   bg=AMBER, font=("Poppins", 9)).pack(side="right")

        sbar = tk.Frame(self._list_view, bg=WHITE)
        sbar.pack(fill="x", padx=30, pady=8)
        self._search_var = tk.StringVar()
        self._search_var.trace("w", lambda *a: self._render_folders())
        se = tk.Entry(sbar, textvariable=self._search_var,
                      font=("Poppins", 10), relief="flat",
                      highlightbackground=CREAM, highlightthickness=1)
        se.pack(side="left", ipady=6, padx=(0, 8), ipadx=10)

        canvas = tk.Canvas(self._list_view, bg=WHITE, highlightthickness=0)
        sb     = ttk.Scrollbar(self._list_view, orient="vertical", command=canvas.yview)
        self._grid_inner = tk.Frame(canvas, bg=WHITE)
        self._grid_inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._grid_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, padx=30)
        sb.pack(side="right", fill="y")

        # ── DETAIL VIEW ────────────────────────────────────
        self._detail_view = tk.Frame(self, bg=WHITE)

        dhdr = tk.Frame(self._detail_view, bg=WHITE)
        dhdr.pack(fill="x", padx=30, pady=(20, 0))
        styled_btn(dhdr, "‹", self._show_list, bg=CREAM, fg=TEXT_DARK,
                   font=("Poppins", 16)).pack(side="left")
        self._detail_title = tk.Label(dhdr, text="Wallet", bg=WHITE,
                                      fg=TEXT_DARK, font=("Georgia", 18, "italic"))
        self._detail_title.pack(side="left", padx=12)
        styled_btn(dhdr, "+ Add Transaction",
                   self._open_add_tx, bg=ACTIVE_NAV,
                   font=("Poppins", 9)).pack(side="right", padx=6)

        tab_row = tk.Frame(self._detail_view, bg=WHITE,
                           highlightbackground=CREAM, highlightthickness=1)
        tab_row.pack(fill="x", padx=30, pady=10)
        self._detail_tabs  = {}
        self._detail_panes = {}
        for key, lbl in [("transactions", "Transactions"),
                          ("reports",      "Reports"),
                          ("receipts",     "Receipts"),
                          ("archives",     "Archive")]:
            b = tk.Button(tab_row, text=lbl, relief="flat",
                          font=("Poppins", 10), cursor="hand2",
                          padx=16, pady=8,
                          command=lambda k=key: self._switch_detail_tab(k))
            b.pack(side="left")
            self._detail_tabs[key] = b

        self._detail_body = tk.Frame(self._detail_view, bg=WHITE)
        self._detail_body.pack(fill="both", expand=True, padx=30)

        # Transactions pane
        tp = tk.Frame(self._detail_body, bg=WHITE)
        self._detail_panes["transactions"] = tp
        tf = tk.Frame(tp, bg=WHITE)
        tf.pack(fill="x", pady=6)
        self._tx_filter_btns = {}
        for f in ("all", "income", "expense"):
            b = tk.Button(tf, text=f.capitalize(), relief="flat",
                          font=("Poppins", 9), cursor="hand2",
                          padx=18, pady=5,
                          command=lambda x=f: self._set_tx_filter(x))
            b.pack(side="left", padx=4)
            self._tx_filter_btns[f] = b
        self._set_tx_filter("all")
        tc = tk.Canvas(tp, bg=WHITE, highlightthickness=0)
        ts = ttk.Scrollbar(tp, orient="vertical", command=tc.yview)
        self._tx_list = tk.Frame(tc, bg=WHITE)
        self._tx_list.bind("<Configure>",
            lambda e: tc.configure(scrollregion=tc.bbox("all")))
        tc.create_window((0, 0), window=self._tx_list, anchor="nw")
        tc.configure(yscrollcommand=ts.set)
        tc.pack(side="left", fill="both", expand=True)
        ts.pack(side="right", fill="y")

        # Reports pane
        rp = tk.Frame(self._detail_body, bg=WHITE)
        self._detail_panes["reports"] = rp
        self._build_reports_pane(rp)

        # Receipts pane
        rcp = tk.Frame(self._detail_body, bg=WHITE)
        self._detail_panes["receipts"] = rcp
        tk.Label(rcp,
                 text="Receipts are stored in Supabase Storage.\nOpen the web app to view receipt images.",
                 bg=WHITE, fg=TEXT_MUTE, font=("Poppins", 10),
                 justify="center").pack(pady=60)

        # Archives pane
        ap = tk.Frame(self._detail_body, bg=WHITE)
        self._detail_panes["archives"] = ap
        self._build_archives_pane(ap)

        self._switch_detail_tab("transactions")

    def _build_reports_pane(self, parent):
        bar = tk.Frame(parent, bg=AMBER_LIGHT)
        bar.pack(fill="x", pady=10)
        tk.Label(bar, text="Generate Financial Report", bg=AMBER_LIGHT,
                 fg=TEXT_DARK, font=("Poppins", 12, "bold"),
                 padx=16, pady=14).pack(side="left")
        styled_btn(bar, "Generate Report",
                   self._generate_report, bg=WHITE, fg=TEXT_DARK,
                   font=("Poppins", 9)).pack(side="right", padx=8, pady=10)

        stats = tk.Frame(parent, bg=WHITE)
        stats.pack(fill="x", pady=10)
        self._stat_vars = {}
        for key, lbl in [("budget",  "Budget"),
                          ("income",  "Total Income"),
                          ("expense", "Total Expenses"),
                          ("ending",  "Ending Cash")]:
            c = tk.Frame(stats, bg=WHITE,
                         highlightbackground=CREAM, highlightthickness=2)
            c.pack(side="left", fill="both", expand=True, padx=6, pady=4)
            tk.Label(c, text=lbl, bg=WHITE, fg=TEXT_MUTE,
                     font=("Poppins", 9), pady=6).pack()
            var = tk.StringVar(value="Php 0.00")
            self._stat_vars[key] = var
            tk.Label(c, textvariable=var, bg=WHITE, fg=TEXT_DARK,
                     font=("Poppins", 11, "bold"), pady=6).pack()

        styled_btn(parent, "Submit Report to OSAS",
                   self._submit_report, bg=GREEN_OK,
                   font=("Poppins", 10, "bold")).pack(pady=12, ipady=4)

    def _build_archives_pane(self, parent):
        tk.Label(parent, text="Submitted Reports", bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 12, "bold")).pack(anchor="w", pady=(8, 6))
        styled_btn(parent, "↻ Load Archives",
                   self._load_archives, bg=AMBER,
                   font=("Poppins", 9)).pack(anchor="e", pady=4)
        canvas = tk.Canvas(parent, bg=WHITE, highlightthickness=0)
        sb     = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self._arch_list = tk.Frame(canvas, bg=WHITE)
        self._arch_list.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._arch_list, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _show_list(self):
        self._detail_view.pack_forget()
        self._list_view.pack(fill="both", expand=True)

    def _show_detail(self, folder):
        self._sel_folder = folder
        self._list_view.pack_forget()
        self._detail_title.config(
            text=f"{folder.get('wallet_name', '')} / {folder.get('name', '')} {folder.get('year', '')}")
        self._detail_view.pack(fill="both", expand=True)
        self._switch_detail_tab("transactions")
        self._load_transactions()
        self._load_report_stats()

    def _switch_detail_tab(self, key):
        for k, b in self._detail_tabs.items():
            if k == key:
                b.config(bg=WHITE, fg=TEXT_DARK,
                         highlightbackground=AMBER, highlightthickness=2)
            else:
                b.config(bg=WHITE, fg=TEXT_MUTE,
                         highlightbackground=CREAM, highlightthickness=0)
        for k, p in self._detail_panes.items():
            if k == key:
                p.pack(fill="both", expand=True)
            else:
                p.pack_forget()

    def _set_tx_filter(self, f):
        self._tx_filter = f
        for k, b in self._tx_filter_btns.items():
            b.config(bg=AMBER if k == f else WHITE,
                     fg=WHITE if k == f else TEXT_MUTE)
        if self._sel_folder:
            self._load_transactions()

    def load_folders(self):
        org_id = self.org["id"]
        try:
            wres = supabase.table("wallets").select("id,name") \
                           .eq("organization_id", org_id).execute()
            self._folders = []
            for w in (wres.data or []):
                bres = supabase.table("wallet_budgets") \
                               .select("id,amount,year,month_id,months(month_name,month_order)") \
                               .eq("wallet_id", w["id"]).execute()
                for b in (bres.data or []):
                    self._folders.append({
                        "id":          b["id"],
                        "wallet_id":   w["id"],
                        "wallet_name": w["name"],
                        "name":        b["months"]["month_name"],
                        "year":        b["year"],
                        "amount":      float(b.get("amount") or 0),
                    })
            self._render_folders()
        except Exception as e:
            messagebox.showerror("Wallets Error", str(e))

    def _render_folders(self):
        for w in self._grid_inner.winfo_children():
            w.destroy()
        q     = self._search_var.get().lower()
        shown = [f for f in self._folders
                 if q in f["wallet_name"].lower() or q in f["name"].lower()]
        if not shown:
            tk.Label(self._grid_inner, text="No wallets found.",
                     bg=WHITE, fg=TEXT_MUTE,
                     font=("Poppins", 10)).pack(pady=40)
            return

        colors    = [AMBER_LIGHT, CREAM, "#E8F5E9", "#E3F2FD", "#FFF3E0"]
        row_frame = None
        for i, f in enumerate(shown):
            if i % 4 == 0:
                row_frame = tk.Frame(self._grid_inner, bg=WHITE)
                row_frame.pack(fill="x", pady=8, padx=4)
            bg_col = colors[i % len(colors)]
            card = tk.Frame(row_frame, bg=bg_col, width=170, height=130,
                            cursor="hand2",
                            highlightbackground="#CCC", highlightthickness=1)
            card.pack(side="left", padx=8)
            card.pack_propagate(False)
            card.bind("<Button-1>", lambda e, folder=f: self._show_detail(folder))
            tk.Label(card, text=f["name"], bg=bg_col, fg=TEXT_DARK,
                     font=("Poppins", 10, "bold"), wraplength=140,
                     justify="center").place(relx=0.5, rely=0.3, anchor="center")
            tk.Label(card, text=f["wallet_name"], bg=bg_col, fg=TEXT_MUTE,
                     font=("Poppins", 8)).place(relx=0.5, rely=0.55, anchor="center")
            tk.Label(card, text=f"{f['year']}", bg=bg_col, fg=TEXT_MUTE,
                     font=("Poppins", 8)).place(relx=0.5, rely=0.70, anchor="center")

    def _load_transactions(self):
        for w in self._tx_list.winfo_children():
            w.destroy()
        if not self._sel_folder:
            return
        fid = self._sel_folder["id"]
        wid = self._sel_folder["wallet_id"]
        try:
            res = supabase.table("wallet_transactions") \
                          .select("id,kind,date_issued,description,quantity,price,income_type,particulars") \
                          .eq("wallet_id", wid) \
                          .eq("budget_id", fid) \
                          .order("date_issued").execute()
            txs = res.data or []
            if self._tx_filter != "all":
                txs = [t for t in txs if t.get("kind") == self._tx_filter]
            if not txs:
                tk.Label(self._tx_list, text="No transactions.",
                         bg=WHITE, fg=TEXT_MUTE,
                         font=("Poppins", 10)).pack(pady=30)
                return
            for tx in txs:
                qty   = int(tx.get("quantity") or 0)
                price = float(tx.get("price") or 0)
                amt   = qty * price
                kind  = tx.get("kind", "")
                color = GREEN_OK if kind == "income" else RED_ERR
                sign  = "+" if kind == "income" else "-"

                row = tk.Frame(self._tx_list, bg=WHITE,
                               highlightbackground=CREAM, highlightthickness=1)
                row.pack(fill="x", pady=3, padx=2)
                left = tk.Frame(row, bg=WHITE)
                left.pack(side="left", padx=10, pady=6, fill="both", expand=True)
                desc = tx.get("description") or tx.get("particulars", "")
                tk.Label(left, text=desc[:44], bg=WHITE, fg=TEXT_DARK,
                         font=("Poppins", 9, "bold"), anchor="w").pack(anchor="w")
                sub = tx.get("income_type", "") or kind.capitalize()
                tk.Label(left, text=f"{sub}  ·  {tx.get('date_issued', '')[:10]}",
                         bg=WHITE, fg=TEXT_MUTE,
                         font=("Poppins", 8)).pack(anchor="w")
                tk.Label(row, text=f"{sign}Php {amt:,.2f}",
                         bg=WHITE, fg=color,
                         font=("Poppins", 10, "bold"), padx=10).pack(side="right")
        except Exception as e:
            messagebox.showerror("Transactions Error", str(e))

    def _load_report_stats(self):
        if not self._sel_folder:
            return
        fid = self._sel_folder["id"]
        wid = self._sel_folder["wallet_id"]
        try:
            res = supabase.table("wallet_transactions") \
                          .select("kind,quantity,price") \
                          .eq("wallet_id", wid) \
                          .eq("budget_id", fid).execute()
            total_inc = total_exp = 0.0
            for tx in (res.data or []):
                qty   = int(tx.get("quantity") or 0)
                price = float(tx.get("price") or 0)
                amt   = qty * price
                if tx.get("kind") == "income":
                    total_inc += amt
                else:
                    total_exp += amt
            budget = self._sel_folder.get("amount", 0)
            ending = budget + total_inc - total_exp
            self._stat_vars["budget"].set(f"Php {budget:,.2f}")
            self._stat_vars["income"].set(f"Php {total_inc:,.2f}")
            self._stat_vars["expense"].set(f"Php {total_exp:,.2f}")
            self._stat_vars["ending"].set(f"Php {ending:,.2f}")
        except Exception:
            pass

    def _load_archives(self):
        for w in self._arch_list.winfo_children():
            w.destroy()
        if not self._sel_folder:
            return
        fid = self._sel_folder["id"]
        wid = self._sel_folder["wallet_id"]
        org = self.org["id"]
        try:
            res = supabase.table("financial_report_archives") \
                          .select("id,report_no,event_name,date_prepared,budget,total_expense,remaining") \
                          .eq("organization_id", org) \
                          .eq("wallet_id", wid) \
                          .eq("budget_id", fid) \
                          .order("created_at").execute()
            archives = res.data or []
            if not archives:
                tk.Label(self._arch_list, text="No submitted reports.",
                         bg=WHITE, fg=TEXT_MUTE,
                         font=("Poppins", 10)).pack(pady=30)
                return
            for a in archives:
                card = tk.Frame(self._arch_list, bg=WHITE,
                                highlightbackground=CREAM, highlightthickness=2)
                card.pack(fill="x", pady=6, padx=2)
                tk.Label(card, text=a.get("report_no", "—"), bg=WHITE,
                         fg=TEXT_DARK, font=("Poppins", 11, "bold"),
                         padx=12, pady=6).pack(anchor="w")
                tk.Label(card, text=f"Event: {a.get('event_name', '—')}",
                         bg=WHITE, fg=TEXT_MUTE,
                         font=("Poppins", 9), padx=12).pack(anchor="w")
                tk.Label(card,
                         text=f"Budget: Php {float(a.get('budget') or 0):,.2f}  |  "
                              f"Expense: Php {float(a.get('total_expense') or 0):,.2f}  |  "
                              f"Remaining: Php {float(a.get('remaining') or 0):,.2f}",
                         bg=WHITE, fg=TEXT_DARK,
                         font=("Poppins", 9), padx=12, pady=6).pack(anchor="w")
        except Exception as e:
            messagebox.showerror("Archives Error", str(e))

    def _open_add_tx(self):
        if not self._sel_folder:
            messagebox.showwarning("No folder", "Select a wallet folder first.")
            return
        AddTransactionDialog(self, self._sel_folder, self.org,
                             on_done=self._load_transactions)

    def _generate_report(self):
        if not self._sel_folder:
            messagebox.showwarning("No folder", "Select a wallet folder first.")
            return
        messagebox.showinfo("Generate Report",
            "Report generation requires the web app (DOCX template).\n"
            "Please use the web version to generate and download the DOCX report.")

    def _submit_report(self):
        if not self._sel_folder:
            messagebox.showwarning("No folder", "Select a wallet folder first.")
            return
        if not messagebox.askyesno("Submit Report",
                "Submit this report to OSAS?\nYou will not be able to edit after submission."):
            return
        wid = self._sel_folder["wallet_id"]
        org = self.org["id"]
        try:
            res = supabase.table("financial_reports") \
                          .select("*") \
                          .eq("organization_id", org) \
                          .eq("wallet_id", wid) \
                          .eq("status", "Pending Review") \
                          .order("created_at", desc=True).limit(1).execute()
            if not res.data:
                messagebox.showinfo("No Report", "No pending report found. Generate one first.")
                return
            rep_id = res.data[0]["id"]
            supabase.table("financial_reports").update({
                "status":          "Submitted",
                "submission_date": datetime.utcnow().date().isoformat(),
                "updated_at":      datetime.utcnow().isoformat(),
            }).eq("id", rep_id).execute()
            messagebox.showinfo("Submitted ✓", "Report submitted to OSAS successfully!")
        except Exception as e:
            messagebox.showerror("Submit Error", str(e))


# ═══════════════════════════════════════════════════════════
# ADD TRANSACTION DIALOG
# ═══════════════════════════════════════════════════════════
class AddTransactionDialog(tk.Toplevel):
    def __init__(self, parent, folder, org, on_done):
        super().__init__(parent)
        self.folder  = folder
        self.org     = org
        self.on_done = on_done
        self.title("Add Transaction")
        self.geometry("440x520")
        self.configure(bg=WHITE)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Add Transaction", bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 14, "bold")).pack(pady=(20, 4))
        tk.Label(self, text="Add a new transaction for this wallet.",
                 bg=WHITE, fg=TEXT_MUTE, font=("Poppins", 9)).pack(pady=(0, 14))

        form = tk.Frame(self, bg=WHITE)
        form.pack(padx=30, fill="x")

        def row(label):
            tk.Label(form, text=label, bg=WHITE, fg=TEXT_MUTE,
                     font=("Poppins", 9)).pack(anchor="w", pady=(6, 2))

        row("Kind")
        self.kind_var = tk.StringVar(value="expense")
        kind_frame = tk.Frame(form, bg=WHITE)
        kind_frame.pack(fill="x")
        for k in ("income", "expense"):
            tk.Radiobutton(kind_frame, text=k.capitalize(), variable=self.kind_var,
                           value=k, bg=WHITE, font=("Poppins", 10)).pack(side="left", padx=8)

        row("Date Issued")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(form, textvariable=self.date_var, font=("Poppins", 10),
                 relief="flat", highlightbackground=CREAM,
                 highlightthickness=1).pack(fill="x", ipady=6)

        row("Quantity")
        self.qty_var = tk.StringVar(value="1")
        tk.Entry(form, textvariable=self.qty_var, font=("Poppins", 10),
                 relief="flat", highlightbackground=CREAM,
                 highlightthickness=1).pack(fill="x", ipady=6)

        row("Description")
        self.desc_var = tk.StringVar()
        tk.Entry(form, textvariable=self.desc_var, font=("Poppins", 10),
                 relief="flat", highlightbackground=CREAM,
                 highlightthickness=1).pack(fill="x", ipady=6)

        row("Particulars (expense only)")
        self.part_var = tk.StringVar()
        tk.Entry(form, textvariable=self.part_var, font=("Poppins", 10),
                 relief="flat", highlightbackground=CREAM,
                 highlightthickness=1).pack(fill="x", ipady=6)

        row("Income Type (income only)")
        self.itype_var = tk.StringVar()
        ttk.Combobox(form, textvariable=self.itype_var,
                     values=["IGP", "Registration Fee", "Membership Fee"],
                     state="readonly", font=("Poppins", 10)).pack(fill="x", ipady=4)

        row("Price")
        self.price_var = tk.StringVar(value="0.00")
        tk.Entry(form, textvariable=self.price_var, font=("Poppins", 10),
                 relief="flat", highlightbackground=CREAM,
                 highlightthickness=1).pack(fill="x", ipady=6)

        btn_row = tk.Frame(self, bg=WHITE)
        btn_row.pack(pady=16)
        styled_btn(btn_row, "Cancel", self.destroy,
                   bg=CREAM, fg=TEXT_DARK).pack(side="left", padx=8)
        styled_btn(btn_row, "Save", self._save,
                   bg=ACTIVE_NAV).pack(side="left", padx=8)

    def _save(self):
        try:
            fid   = self.folder["id"]
            wid   = self.folder["wallet_id"]
            kind  = self.kind_var.get()
            date  = self.date_var.get().strip()
            qty   = int(self.qty_var.get() or 1)
            desc  = self.desc_var.get().strip()
            price = float(self.price_var.get() or 0)
            itype = self.itype_var.get()
            part  = self.part_var.get().strip()

            if not desc:
                messagebox.showwarning("Required", "Description is required.")
                return
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Invalid Date", "Date must be in YYYY-MM-DD format.")
                return

            supabase.table("wallet_transactions").insert({
                "wallet_id":   wid,
                "budget_id":   fid,
                "kind":        kind,
                "date_issued": date,
                "quantity":    qty,
                "description": desc,
                "price":       price,
                "income_type": itype if kind == "income" else None,
                "particulars": part  if kind == "expense" else None,
            }).execute()
            messagebox.showinfo("Saved ✓", "Transaction added successfully!")
            self.destroy()
            self.on_done()
        except Exception as e:
            messagebox.showerror("Error", str(e))