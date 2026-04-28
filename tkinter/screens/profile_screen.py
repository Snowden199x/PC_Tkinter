"""
profile_screen.py — Profile tab and Add Officer dialog.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from constants import (
    WHITE, CREAM, AMBER,
    TEXT_DARK, TEXT_MUTE, ACTIVE_NAV, GREEN_OK,
    styled_btn, supabase
)


# ═══════════════════════════════════════════════════════════
# PROFILE TAB
# ═══════════════════════════════════════════════════════════
class ProfileTab(tk.Frame):
    def __init__(self, parent, org):
        super().__init__(parent, bg=WHITE)
        self.org      = org
        self._editing = False
        self._build()
        self.load()

    def _build(self):
        tk.Label(self, text="Profile", bg=WHITE, fg=TEXT_DARK,
                 font=("Georgia", 22, "italic")).pack(anchor="w", padx=30, pady=(24, 0))

        # Banner
        banner = tk.Frame(self, bg=CREAM)
        banner.pack(fill="x", padx=30, pady=14)

        self._photo_label = tk.Label(banner, bg=CREAM, width=10, height=5,
                                     relief="flat",
                                     highlightbackground=WHITE,
                                     highlightthickness=3)
        self._photo_label.pack(side="left", padx=20, pady=16)

        info = tk.Frame(banner, bg=CREAM)
        info.pack(side="left", fill="both", expand=True, pady=16)

        self._ov_name  = tk.Label(info, text="", bg=CREAM, fg=TEXT_DARK,
                                   font=("Poppins", 16, "bold"))
        self._ov_name.pack(anchor="w")
        self._ov_short = tk.Label(info, text="", bg=CREAM, fg=ACTIVE_NAV,
                                   font=("Poppins", 12, "bold"))
        self._ov_short.pack(anchor="w")
        self._ov_dept  = tk.Label(info, text="", bg=CREAM, fg=TEXT_MUTE,
                                   font=("Poppins", 10))
        self._ov_dept.pack(anchor="w")
        self._ov_email = tk.Label(info, text="", bg=CREAM, fg=TEXT_MUTE,
                                   font=("Poppins", 10))
        self._ov_email.pack(anchor="w")
        tk.Label(info, text="✓ Accredited", bg="#4CAF50", fg=WHITE,
                 font=("Poppins", 9, "bold"), padx=10, pady=4).pack(anchor="w", pady=6)

        # Tabs
        tab_bar = tk.Frame(self, bg=WHITE,
                           highlightbackground=CREAM, highlightthickness=1)
        tab_bar.pack(fill="x", padx=30, pady=(0, 6))
        self._tabs     = {}
        self._panes    = {}
        self._tab_body = tk.Frame(self, bg=WHITE)
        self._tab_body.pack(fill="both", expand=True, padx=30)

        for key, lbl in [("org",      "Organization Info"),
                          ("officers", "Officers"),
                          ("accred",   "Accreditation")]:
            b = tk.Button(tab_bar, text=lbl, relief="flat",
                          font=("Poppins", 10), cursor="hand2",
                          padx=14, pady=8,
                          command=lambda k=key: self._switch_tab(k))
            b.pack(side="left")
            self._tabs[key] = b

        # ── Org Info pane ──
        op = tk.Frame(self._tab_body, bg=WHITE)
        self._panes["org"] = op
        self._vars = {}
        fields = [
            ("org_name",       "Organization Name",  False),
            ("org_short_name", "Shortened Name",      True),
            ("department",     "Department",          False),
            ("school",         "School/University",   False),
            ("email",          "Email Address",       True),
        ]
        for key, lbl, editable in fields:
            tk.Label(op, text=lbl, bg=WHITE, fg=TEXT_MUTE,
                     font=("Poppins", 9)).pack(anchor="w", pady=(8, 2))
            var = tk.StringVar()
            self._vars[key] = var
            e = tk.Entry(op, textvariable=var, font=("Poppins", 10),
                         relief="flat", bg="#F9F9F9",
                         highlightbackground=CREAM, highlightthickness=1,
                         state="readonly" if not editable else "normal")
            e.pack(fill="x", ipady=6)
            setattr(self, f"_entry_{key}", e)

        self._edit_btn = styled_btn(op, "Edit", self._toggle_edit, bg=ACTIVE_NAV)
        self._edit_btn.pack(anchor="e", pady=10)

        # ── Officers pane ──
        offp = tk.Frame(self._tab_body, bg=WHITE)
        self._panes["officers"] = offp
        off_hdr = tk.Frame(offp, bg=WHITE)
        off_hdr.pack(fill="x", pady=8)
        tk.Label(off_hdr, text="Organization Officers", bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 12, "bold")).pack(side="left")
        styled_btn(off_hdr, "+ Add Officer",
                   self._add_officer, bg=ACTIVE_NAV,
                   font=("Poppins", 9)).pack(side="right")
        cols = ("Name", "Position", "Term Start", "Term End", "Status")
        self._off_tree = ttk.Treeview(offp, columns=cols, show="headings", height=8)
        for c in cols:
            self._off_tree.heading(c, text=c)
            self._off_tree.column(c, width=120, anchor="center")
        self._off_tree.pack(fill="both", expand=True)
        styled_btn(offp, "↻ Refresh Officers",
                   self._load_officers, bg=AMBER,
                   font=("Poppins", 9)).pack(anchor="e", pady=4)

        # ── Accreditation pane ──
        acp = tk.Frame(self._tab_body, bg=WHITE)
        self._panes["accred"] = acp
        card = tk.Frame(acp, bg=WHITE,
                        highlightbackground=CREAM, highlightthickness=2)
        card.pack(fill="x", pady=20)
        tk.Label(card, text="Accreditation Information", bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 12, "bold"),
                 padx=20, pady=10).pack(anchor="w")
        tk.Frame(card, bg=CREAM, height=1).pack(fill="x")
        self._acc_date   = tk.Label(card, text="", bg=WHITE, fg=TEXT_DARK,
                                     font=("Poppins", 10), padx=20, pady=8)
        self._acc_date.pack(anchor="w")
        self._acc_status = tk.Label(card, text="", bg=WHITE, fg=GREEN_OK,
                                     font=("Poppins", 10, "bold"), padx=20, pady=4)
        self._acc_status.pack(anchor="w")

        self._switch_tab("org")

    def _switch_tab(self, key):
        for k, b in self._tabs.items():
            b.config(bg=WHITE,
                     fg=ACTIVE_NAV if k == key else TEXT_MUTE,
                     font=("Poppins", 10, "bold" if k == key else "normal"))
        for k, p in self._panes.items():
            if k == key:
                p.pack(fill="both", expand=True)
            else:
                p.pack_forget()
        if key == "officers":
            self._load_officers()

    def load(self):
        org_id = self.org["id"]
        try:
            org_res = supabase.table("organizations") \
                              .select("id,org_name,department_id,accreditation_date,status") \
                              .eq("id", org_id).limit(1).execute()
            if not org_res.data:
                return
            org = org_res.data[0]

            prof_res = supabase.table("profile_users") \
                               .select("org_short_name,campus,school_name,email") \
                               .eq("organization_id", org_id).limit(1).execute()
            prof = prof_res.data[0] if prof_res.data else {}

            dept_name = ""
            if org.get("department_id"):
                dr = supabase.table("departments") \
                             .select("dept_name") \
                             .eq("id", org["department_id"]).limit(1).execute()
                if dr.data:
                    dept_name = dr.data[0]["dept_name"]

            self._vars["org_name"].set(org.get("org_name", ""))
            self._vars["org_short_name"].set(prof.get("org_short_name", ""))
            self._vars["department"].set(dept_name)
            self._vars["school"].set(prof.get("school_name", ""))
            self._vars["email"].set(prof.get("email", ""))

            self._ov_name.config(text=org.get("org_name", ""))
            self._ov_short.config(text=prof.get("org_short_name", ""))
            self._ov_dept.config(text=dept_name)
            self._ov_email.config(text=prof.get("email", ""))

            self._acc_date.config(
                text=f"Date of Accreditation:  {org.get('accreditation_date', '—')}")
            status_txt = "Accredited" if org.get("status") == "Active" else org.get("status", "")
            self._acc_status.config(text=f"Current Status:  {status_txt}")
        except Exception as e:
            messagebox.showerror("Profile Error", str(e))

    def _toggle_edit(self):
        self._editing = not self._editing
        state = "normal" if self._editing else "readonly"
        for key in ("org_short_name", "email"):
            getattr(self, f"_entry_{key}").config(state=state)
        self._edit_btn.config(
            text="Save Changes" if self._editing else "Edit",
            bg=GREEN_OK if self._editing else ACTIVE_NAV)
        if not self._editing:
            self._save_profile()

    def _save_profile(self):
        org_id = self.org["id"]
        try:
            supabase.table("profile_users").update({
                "org_short_name": self._vars["org_short_name"].get(),
                "email":          self._vars["email"].get(),
            }).eq("organization_id", org_id).execute()
            messagebox.showinfo("Saved ✓", "Profile updated successfully!")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _load_officers(self):
        for row in self._off_tree.get_children():
            self._off_tree.delete(row)
        org_id = self.org["id"]
        try:
            res = supabase.table("profile_officers") \
                          .select("id,name,position,term_start,term_end,status") \
                          .eq("organization_id", org_id) \
                          .order("term_start").execute()
            for o in (res.data or []):
                self._off_tree.insert("", "end", values=(
                    o.get("name", ""),
                    o.get("position", ""),
                    str(o.get("term_start", ""))[:7],
                    str(o.get("term_end", ""))[:7],
                    o.get("status", ""),
                ))
        except Exception as e:
            messagebox.showerror("Officers Error", str(e))

    def _add_officer(self):
        AddOfficerDialog(self, self.org, on_done=self._load_officers)


# ═══════════════════════════════════════════════════════════
# ADD OFFICER DIALOG
# ═══════════════════════════════════════════════════════════
class AddOfficerDialog(tk.Toplevel):
    def __init__(self, parent, org, on_done):
        super().__init__(parent)
        self.org     = org
        self.on_done = on_done
        self.title("Add Officer")
        self.geometry("400x400")
        self.configure(bg=WHITE)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Add Officer", bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 13, "bold")).pack(pady=(20, 14))
        form = tk.Frame(self, bg=WHITE)
        form.pack(padx=30, fill="x")
        self._vars = {}
        for key, lbl in [("name",       "Name"),
                          ("position",   "Position"),
                          ("term_start", "Term Start (YYYY-MM)"),
                          ("term_end",   "Term End (YYYY-MM)")]:
            tk.Label(form, text=lbl, bg=WHITE, fg=TEXT_MUTE,
                     font=("Poppins", 9)).pack(anchor="w", pady=(6, 2))
            var = tk.StringVar()
            self._vars[key] = var
            tk.Entry(form, textvariable=var, font=("Poppins", 10),
                     relief="flat", highlightbackground=CREAM,
                     highlightthickness=1).pack(fill="x", ipady=6)
        tk.Label(form, text="Status", bg=WHITE, fg=TEXT_MUTE,
                 font=("Poppins", 9)).pack(anchor="w", pady=(6, 2))
        self._status_var = tk.StringVar(value="Active")
        ttk.Combobox(form, textvariable=self._status_var,
                     values=["Active", "Inactive"],
                     state="readonly").pack(fill="x")
        row = tk.Frame(self, bg=WHITE)
        row.pack(pady=16)
        styled_btn(row, "Cancel", self.destroy,
                   bg=CREAM, fg=TEXT_DARK).pack(side="left", padx=8)
        styled_btn(row, "Save Officer", self._save,
                   bg=ACTIVE_NAV).pack(side="left", padx=8)

    def _save(self):
        try:
            name = self._vars["name"].get().strip()
            if not name:
                messagebox.showwarning("Required", "Name is required.")
                return
            supabase.table("profile_officers").insert({
                "organization_id": self.org["id"],
                "name":       name,
                "position":   self._vars["position"].get(),
                "term_start": self._vars["term_start"].get() or None,
                "term_end":   self._vars["term_end"].get() or None,
                "status":     self._status_var.get(),
            }).execute()
            messagebox.showinfo("Saved ✓", "Officer added!")
            self.destroy()
            self.on_done()
        except Exception as e:
            messagebox.showerror("Error", str(e))