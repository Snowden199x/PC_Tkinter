import tkinter as tk
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageTk
from db import change_password

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS   = os.path.join(BASE_DIR, "assets", "images")

BG_COLOR      = "#f7f3eb"
PRIMARY       = "#8B3B08"
PRIMARY_HOVER = "#E59E2C"
TEXT_MUTED    = "#616161"
ERROR_CLR     = "#e05c5c"
SUCCESS_CLR   = "#2E7D32"


class ChangePasswordScreen(tk.Frame):
    def __init__(self, parent, org, on_success, **kwargs):
        super().__init__(parent, bg=BG_COLOR, **kwargs)
        self._org        = org
        self._on_success = on_success
        self._images     = {}
        self._build()

    # ── image helpers ─────────────────────────────────────────────────
    def _img(self, name, w=None, h=None):
        path = os.path.join(ASSETS, name)
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path)
            if w and h:
                img = img.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            self._images[name] = ph
            return ph
        except Exception:
            return None

    def _base_img(self, name, w=None, h=None):
        path = os.path.join(BASE_DIR, name)
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path)
            if w and h:
                img = img.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            self._images[name] = ph
            return ph
        except Exception:
            return None

    # ── build UI ──────────────────────────────────────────────────────
    def _build(self):
        # background
        bg_img = self._img("log_in_bg.png")
        if bg_img:
            tk.Label(self, image=bg_img).place(relwidth=1, relheight=1)

        # ── logo top-left (no navigation — new user can't go back) ────
        logo_frame = tk.Frame(self, bg=BG_COLOR)
        logo_frame.place(x=20, y=15)

        logo_img = self._base_img("pocki_logo.png", 70, 70)
        if logo_img:
            tk.Label(logo_frame, image=logo_img, bg=BG_COLOR).pack(side="left")
        tk.Label(logo_frame, text="PockiTrack",
                 font=("Poppins", 24, "bold"), bg=BG_COLOR).pack(side="left", padx=8)

        # ── centered card ─────────────────────────────────────────────
        container = tk.Frame(self, bg=BG_COLOR)
        container.place(relx=0.5, rely=0.5, anchor="center")

        shadow = tk.Frame(container, bg="#eaeaea")
        shadow.pack()

        card = tk.Frame(shadow, bg="white", padx=40, pady=35)
        card.pack(padx=4, pady=4)

        # title
        tk.Label(card, text="Create New Password",
                 font=("Poppins", 24, "bold"), bg="white").pack(pady=(5, 8))

        org_name = self._org.get("org_name", "") if self._org else ""
        tk.Label(card,
                 text=f"Welcome, {org_name}!\nPlease set a new password to continue.",
                 font=("Poppins", 10), fg=TEXT_MUTED, bg="white",
                 justify="center").pack(pady=(0, 20))

        # form
        form = tk.Frame(card, bg="white")
        form.pack(fill="x")

        # NEW PASSWORD
        tk.Label(form, text="New Password",
                 font=("Poppins", 10), fg="#828282", bg="white").pack(anchor="w")
        
        
        pw1_frame = tk.Frame(form, bg="white", highlightbackground="#ccc",
                             highlightthickness=1)
        pw1_frame.pack(fill="x", pady=(5, 4))

        self._pw1 = tk.Entry(pw1_frame, show="*", font=("Poppins", 12),
                             bd=0, relief="flat", bg="white")
        self._pw1.pack(side="left", fill="x", expand=True, ipady=6, padx=(4, 0))
        self._pw1.bind("<KeyRelease>", lambda e: (self._clear_error(), self._update_checklist()))

        self._showing1 = False
        eye1_img = self._img("show_password.png", 20, 20)
        eye1_btn = tk.Label(pw1_frame,
                            image=eye1_img if eye1_img else "",
                            text="" if eye1_img else "👁",
                            bg="white", fg="#828282",
                            font=("Poppins", 12), cursor="hand2")
        eye1_btn.pack(side="right", padx=6)

        def _toggle1():
            self._showing1 = not self._showing1
            self._pw1.config(show="" if self._showing1 else "*")
            icon = "hide_password.png" if self._showing1 else "show_password.png"
            new_img = self._img(icon, 20, 20)
            eye1_btn.config(image=new_img if new_img else "",
                            text="" if new_img else ("⌣" if self._showing1 else "👁"))
        eye1_btn.bind("<Button-1>", lambda e: _toggle1())
        
        # CHECKLIST
        checklist_frame = tk.Frame(form, bg="white")
        checklist_frame.pack(fill="x", pady=(4, 12))

        self._checks = {}
        requirements = [
            ("length",    "At least 8 characters"),
            ("uppercase", "At least 1 uppercase letter"),
            ("number",    "At least 1 number"),
            ("special",   "At least 1 special character (@$!%*?&_#^)"),
        ]
        for key, text in requirements:
            row = tk.Frame(checklist_frame, bg="white")
            row.pack(anchor="w")
            dot = tk.Label(row, text="✕", font=("Poppins", 9, "bold"),
                           fg=ERROR_CLR, bg="white", width=2)
            dot.pack(side="left")
            lbl = tk.Label(row, text=text, font=("Poppins", 9),
                           fg=ERROR_CLR, bg="white")
            lbl.pack(side="left")
            self._checks[key] = (dot, lbl)
        # CONFIRM PASSWORD
        tk.Label(form, text="Confirm Password",
                 font=("Poppins", 10), fg="#828282", bg="white").pack(anchor="w")

        pw2_frame = tk.Frame(form, bg="white", highlightbackground="#ccc",
                             highlightthickness=1)
        pw2_frame.pack(fill="x", pady=(5, 6))

        self._pw2 = tk.Entry(pw2_frame, show="*", font=("Poppins", 12),
                             bd=0, relief="flat", bg="white")
        self._pw2.pack(side="left", fill="x", expand=True, ipady=6, padx=(4, 0))
        self._pw2.bind("<KeyRelease>", lambda e: self._clear_error())

        self._showing2 = False
        eye2_img = self._img("show_password.png", 20, 20)
        eye2_btn = tk.Label(pw2_frame,
                            image=eye2_img if eye2_img else "",
                            text="" if eye2_img else "👁",
                            bg="white", fg="#828282",
                            font=("Poppins", 12), cursor="hand2")
        eye2_btn.pack(side="right", padx=6)

        def _toggle2():
            self._showing2 = not self._showing2
            self._pw2.config(show="" if self._showing2 else "*")
            icon = "hide_password.png" if self._showing2 else "show_password.png"
            new_img = self._img(icon, 20, 20)
            eye2_btn.config(image=new_img if new_img else "",
                            text="" if new_img else ("⌣" if self._showing2 else "👁"))
        eye2_btn.bind("<Button-1>", lambda e: _toggle2())

        # error label
        self._error_lbl = tk.Label(form, text="", font=("Poppins", 9),
                                   fg=ERROR_CLR, bg="white", wraplength=300,
                                   justify="left")
        self._error_lbl.pack(anchor="w", pady=(4, 0))

        # submit button
        btn = tk.Canvas(card, width=260, height=45,
                        bg="white", highlightthickness=0)
        btn.pack(pady=(18, 8))

        def _draw_btn(color):
            btn.delete("all")
            btn.create_oval(0, 0, 45, 45, fill=color, outline=color)
            btn.create_oval(215, 0, 260, 45, fill=color, outline=color)
            btn.create_rectangle(22, 0, 238, 45, fill=color, outline=color)
            btn.create_text(130, 22, text="Set New Password",
                            font=("Poppins", 13, "bold"), fill="black")

        _draw_btn("#F3D58D")
        btn.bind("<Enter>",    lambda e: _draw_btn(PRIMARY_HOVER))
        btn.bind("<Leave>",    lambda e: _draw_btn("#F3D58D"))
        btn.bind("<Button-1>", lambda e: self._submit())

    # ── actions ───────────────────────────────────────────────────────
    def _clear_error(self):
        self._error_lbl.config(text="")
        self._pw1.master.config(highlightbackground="#ccc")
        self._pw2.master.config(highlightbackground="#ccc")
        
    def _update_checklist(self):
        import re
        pw = self._pw1.get()
        rules = {
            "length":    len(pw) >= 8,
            "uppercase": bool(re.search(r'[A-Z]', pw)),
            "number":    bool(re.search(r'[0-9]', pw)),
            "special":   bool(re.search(r'[@$!%*?&_#^]', pw)),
        }
        for key, passed in rules.items():
            dot, lbl = self._checks[key]
            if passed:
                dot.config(text="✓", fg=SUCCESS_CLR)
                lbl.config(fg=SUCCESS_CLR)
            else:
                dot.config(text="✕", fg=ERROR_CLR)
                lbl.config(fg=ERROR_CLR)

    def _submit(self):
        import re
        pw1 = self._pw1.get().strip()
        pw2 = self._pw2.get().strip()

        if not pw1 or not (
            len(pw1) >= 8 and
            re.search(r'[A-Z]', pw1) and
            re.search(r'[0-9]', pw1) and
            re.search(r'[@$!%*?&_#^]', pw1)
        ):
            self._error_lbl.config(text="Please meet all password requirements above.")
            self._pw1.master.config(highlightbackground=ERROR_CLR)
            return
        
        if not pw2:
            self._error_lbl.config(text="Please confirm your password.")
            self._pw2.master.config(highlightbackground=ERROR_CLR)
            return
        if pw1 != pw2:
            self._error_lbl.config(text="Passwords do not match.")
            self._pw1.master.config(highlightbackground=ERROR_CLR)
            self._pw2.master.config(highlightbackground=ERROR_CLR)
            return

        try:
            org_id = self._org.get("id") if self._org else None
            if not org_id:
                self._error_lbl.config(text="Session error. Please log in again.")
                return
            change_password(org_id, pw1)
            self._org["must_change_password"] = False
            self._on_success()
        except Exception as e:
            self._error_lbl.config(text=f"Error: {str(e)[:80]}")