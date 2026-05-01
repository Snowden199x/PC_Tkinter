import tkinter as tk
from PIL import Image, ImageTk
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import login_organization

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE_DIR, "assets", "images")

BG_COLOR = "#f7f3eb"
PRIMARY = "#8B3B08"
PRIMARY_HOVER = "#E59E2C"
TEXT_MUTED = "#616161"
BORDER = "#ddd"

class LoginScreen(tk.Frame):
    def __init__(self, parent, on_login_success, on_back):
        super().__init__(parent, bg=BG_COLOR)

        self.on_login_success = on_login_success
        self.on_back = on_back
        self.images = {}

        self._build()

    # ---------- IMAGE LOADER ----------
    def img(self, name, w=None, h=None):
        path = os.path.join(ASSETS, name)
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path)
            if w and h:
                img = img.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            self.images[name] = ph
            return ph
        except Exception:
            return None

    # ---------- BASE IMAGE LOADER ----------
    def base_img(self, name, w=None, h=None):
        """Load image from BASE_DIR (for pocki_logo.png)"""
        path = os.path.join(BASE_DIR, name)
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path)
            if w and h:
                img = img.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            self.images[name] = ph
            return ph
        except Exception:
            return None

    # ---------- UI ----------
    def _build(self):

        # ===== BACKGROUND =====
        bg_img = self.img("log_in_bg.png")
        if bg_img:
            bg_label = tk.Label(self, image=bg_img)
            bg_label.place(relwidth=1, relheight=1)
        else:
            # Fallback background color if image not found
            self.configure(bg=BG_COLOR)

        # ===== LOGO (TOP LEFT) =====
        logo_frame = tk.Frame(self, bg=BG_COLOR, cursor="hand2")
        logo_frame.place(x=20, y=15)

        logo_img = self.base_img("pocki_logo.png", 70, 70)
        if logo_img:
            tk.Label(logo_frame, image=logo_img, bg=BG_COLOR).pack(side="left")
        else:
            tk.Label(logo_frame, text="PT", font=("Poppins", 24, "bold"),
                     bg=BG_COLOR).pack(side="left")

        tk.Label(logo_frame,
                 text="PockiTrack",
                 font=("Poppins", 24, "bold"),
                 bg=BG_COLOR).pack(side="left", padx=8)

        logo_frame.bind("<Button-1>", lambda e: self.on_back())

        # ===== CENTER CONTAINER =====
        container = tk.Frame(self, bg=BG_COLOR)
        container.place(relx=0.5, rely=0.5, anchor="center")

        # ===== LOGIN BOX =====
        box_shadow = tk.Frame(container, bg="#eaeaea")
        box_shadow.pack()

        box = tk.Frame(box_shadow,
                       bg="white",
                       padx=40,
                       pady=35)
        box.pack(padx=4, pady=4)

        # ===== TITLE =====
        tk.Label(box,
                 text="Log in",
                 font=("Poppins", 28, "bold"),
                 bg="white").pack(pady=(5, 5))

        tk.Label(box,
                 text="Enter your details to sign in to your account.",
                 font=("Poppins", 12),
                 fg=TEXT_MUTED,
                 bg="white").pack(pady=(0, 20))

        # ===== FORM =====
        form = tk.Frame(box, bg="white")
        form.pack(fill="x")

        # USERNAME
        tk.Label(form,
                 text="Username",
                 font=("Poppins", 10),
                 fg="#828282",
                 bg="white").pack(anchor="w")

        self.username = tk.Entry(form,
                                 font=("Poppins", 12),
                                 bd=1,
                                 relief="solid")
        self.username.pack(fill="x", pady=(5, 15), ipady=6)
        self.username.bind("<Key>", lambda e: self._clear_error())

        # PASSWORD
        tk.Label(form,
                 text="Password",
                 font=("Poppins", 10),
                 fg="#828282",
                 bg="white").pack(anchor="w")

        pw_frame = tk.Frame(form, bg="white", highlightbackground="#ccc",
                             highlightthickness=1)
        pw_frame.pack(fill="x", pady=(5, 0))

        self.password = tk.Entry(pw_frame,
                                 show="*",
                                 font=("Poppins", 12),
                                 bd=0,
                                 relief="flat",
                                 bg="white")
        self.password.pack(side="left", fill="x", expand=True, ipady=6, padx=(4, 0))
        self.password.bind("<Key>", lambda e: self._clear_error())

        self.showing = False

        eye_img = self.img("show_password.png", 20, 20)
        eye_btn = tk.Label(pw_frame,
                           image=eye_img if eye_img else "",
                           text="" if eye_img else "👁",
                           bg="white",
                           fg="#828282",
                           font=("Poppins", 12),
                           cursor="hand2")
        eye_btn.pack(side="right", padx=6)

        def toggle():
            self.showing = not self.showing
            self.password.config(show="" if self.showing else "*")
            icon = "hide_password.png" if self.showing else "show_password.png"
            new_img = self.img(icon, 20, 20)
            if new_img:
                eye_btn.config(image=new_img, text="")
            else:
                eye_btn.config(text="⌣" if self.showing else "👁")

        eye_btn.bind("<Button-1>", lambda e: toggle())

        # ERROR MESSAGE
        self.error_lbl = tk.Label(form,
                                  text="",
                                  font=("Poppins", 9),
                                  fg="#e05c5c",
                                  bg="white")
        self.error_lbl.pack(anchor="w", pady=(6, 0))

        # FORGOT PASSWORD
        tk.Label(form,
                 text="Forgot password?",
                 fg=PRIMARY,
                 cursor="hand2",
                 font=("Poppins", 9),
                 bg="white").pack(anchor="e", pady=10)

        # ===== BUTTON =====
        btn = tk.Canvas(box, width=220, height=45,
                        bg="white", highlightthickness=0)
        btn.pack(pady=20)

        def draw(color):
            btn.delete("all")
            btn.create_oval(0, 0, 45, 45, fill=color, outline=color)
            btn.create_oval(175, 0, 220, 45, fill=color, outline=color)
            btn.create_rectangle(22, 0, 198, 45, fill=color, outline=color)

            btn.create_text(110, 22,
                            text="Log in",
                            font=("Poppins", 14, "bold"),
                            fill="black")

        draw("#F3D58D")

        btn.bind("<Enter>", lambda e: draw(PRIMARY_HOVER))
        btn.bind("<Leave>", lambda e: draw("#F3D58D"))

        btn.bind("<Button-1>", lambda e: self.login())

    # ---------- CLEAR ERROR ----------
    def _clear_error(self):
        self.error_lbl.config(text="")
        self.username.config(highlightthickness=0)
        self.password.master.config(highlightbackground="#ccc")

    # ---------- LOGIN LOGIC ----------
    def login(self):
        user = self.username.get().strip()
        pw = self.password.get().strip()

        if not user and not pw:
            self.show_error("Please enter your username and password.")
            return
        if not user:
            self.show_error("Please enter your username.")
            return
        if not pw:
            self.show_error("Please enter your password.")
            return

        try:
            org = login_organization(user, pw)
            self.error_lbl.config(text="")
            self.on_login_success(org)
        except ValueError as e:
            self.show_error(str(e))
        except Exception:
            self.show_error("Connection error. Please try again.")

    def show_error(self, message):
        self.error_lbl.config(text=message)
        self.username.config(highlightbackground="#e05c5c", highlightthickness=1)
        self.password.master.config(highlightbackground="#e05c5c")