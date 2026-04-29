import tkinter as tk
from PIL import Image, ImageTk
import os

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
        img = Image.open(path)

        if w and h:
            img = img.resize((w, h))

        ph = ImageTk.PhotoImage(img)
        self.images[name] = ph
        return ph

    # ---------- UI ----------
    def _build(self):

        # ===== BACKGROUND =====
        bg_img = self.img("log_in_bg.png")
        bg_label = tk.Label(self, image=bg_img)
        bg_label.place(relwidth=1, relheight=1)

        # ===== LOGO (TOP LEFT) =====
        logo_frame = tk.Frame(self, bg="", cursor="hand2")
        logo_frame.place(x=20, y=15)

        tk.Label(logo_frame,
                 self.img("../pocki_logo.png", 70, 70),
                 bg="").pack(side="left")

        tk.Label(logo_frame,
                 text="PockiTrack",
                 font=("Poppins", 24, "bold"),
                 bg="").pack(side="left", padx=8)

        logo_frame.bind("<Button-1>", lambda e: self.on_back())

        # ===== CENTER CONTAINER =====
        container = tk.Frame(self, bg="")
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

        # PASSWORD
        tk.Label(form,
                 text="Password",
                 font=("Poppins", 10),
                 fg="#828282",
                 bg="white").pack(anchor="w")

        pw_frame = tk.Frame(form, bg="white")
        pw_frame.pack(fill="x")

        self.password = tk.Entry(pw_frame,
                                 show="*",
                                 font=("Poppins", 12),
                                 bd=1,
                                 relief="solid")
        self.password.pack(side="left", fill="x", expand=True, ipady=6)

        self.showing = False

        eye_btn = tk.Label(pw_frame,
                           image=self.img("show_password.png", 20, 20),
                           bg="white",
                           cursor="hand2")
        eye_btn.pack(side="right", padx=8)

        def toggle():
            self.showing = not self.showing
            self.password.config(show="" if self.showing else "*")

            icon = "hide_password.png" if self.showing else "show_password.png"
            eye_btn.config(image=self.img(icon, 20, 20))

        eye_btn.bind("<Button-1>", lambda e: toggle())

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

    # ---------- LOGIN LOGIC ----------
    def login(self):
        user = self.username.get()
        pw = self.password.get()

        # simple test
        if user == "admin" and pw == "1234":
            self.on_login_success()
        else:
            self.shake()

    # ---------- SHAKE EFFECT ----------
    def shake(self):
        x = self.winfo_x()

        def animate(count=0):
            if count >= 6:
                self.place(x=x)
                return
            offset = (-10 if count % 2 == 0 else 10)
            self.place(x=x + offset)
            self.after(50, lambda: animate(count + 1))

        animate()