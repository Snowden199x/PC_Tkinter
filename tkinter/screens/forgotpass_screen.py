import tkinter as tk
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageTk
from db import request_password_reset

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS   = os.path.join(BASE_DIR, "assets", "images")

BG_COLOR      = "#f7f3eb"
PRIMARY       = "#8B3B08"
PRIMARY_HOVER = "#E59E2C"
TEXT_MUTED    = "#616161"
SUCCESS_CLR   = "#2E7D32"
ERROR_CLR     = "#e05c5c"


class ForgotPassScreen(tk.Frame):
    def __init__(self, parent, on_back, **kwargs):
        super().__init__(parent, bg=BG_COLOR, **kwargs)
        self._on_back = on_back
        self._images  = {}
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
        path = os.path.join(BASE_DIR, "assets", "images", name)
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
        # background image (same as login)
        bg_img = self._img("log_in_bg.png")
        if bg_img:
            tk.Label(self, image=bg_img).place(relwidth=1, relheight=1)

        # ── logo top-left ─────────────────────────────────────────────
        logo_frame = tk.Frame(self, bg=BG_COLOR, cursor="hand2")
        logo_frame.place(x=20, y=15)

        logo_img = self._base_img("pocki_logo.png", 70, 70)
        if logo_img:
            tk.Label(logo_frame, image=logo_img, bg=BG_COLOR).pack(side="left")
        tk.Label(logo_frame, text="PockiTrack",
                 font=("Poppins", 24, "bold"), bg=BG_COLOR).pack(side="left", padx=8)
        logo_frame.bind("<Button-1>", lambda e: self._on_back())
        for child in logo_frame.winfo_children():
            child.bind("<Button-1>", lambda e: self._on_back())

        # ── centered card ─────────────────────────────────────────────
        container = tk.Frame(self, bg=BG_COLOR)
        container.place(relx=0.5, rely=0.5, anchor="center")

        shadow = tk.Frame(container, bg="#eaeaea")
        shadow.pack()

        card = tk.Frame(shadow, bg="white", padx=40, pady=35)
        card.pack(padx=4, pady=4)

        # title
        tk.Label(card, text="Password Restoration",
                 font=("Poppins", 24, "bold"), bg="white").pack(pady=(5, 8))

        tk.Label(card,
                 text="Enter your username or email and you will receive\n"
                      "reset instructions to your registered email.",
                 font=("Poppins", 10), fg=TEXT_MUTED, bg="white",
                 justify="center").pack(pady=(0, 20))

        # form
        form = tk.Frame(card, bg="white")
        form.pack(fill="x")

        tk.Label(form, text="Username or Email",
                 font=("Poppins", 10), fg="#828282", bg="white").pack(anchor="w")

        self._entry = tk.Entry(form, font=("Poppins", 12), bd=1, relief="solid")
        self._entry.pack(fill="x", pady=(5, 6), ipady=6)
        self._entry.bind("<Key>", lambda e: self._clear_messages())

        # error / success labels
        self._error_lbl = tk.Label(form, text="", font=("Poppins", 9),
                                   fg=ERROR_CLR, bg="white", wraplength=300,
                                   justify="left")
        self._error_lbl.pack(anchor="w")

        self._success_lbl = tk.Label(form, text="", font=("Poppins", 9),
                                     fg=SUCCESS_CLR, bg="white", wraplength=300,
                                     justify="left")
        self._success_lbl.pack(anchor="w")

        # submit button — same pill style as login
        btn = tk.Canvas(card, width=260, height=45,
                        bg="white", highlightthickness=0)
        btn.pack(pady=(18, 8))

        def _draw_btn(color):
            btn.delete("all")
            btn.create_oval(0, 0, 45, 45, fill=color, outline=color)
            btn.create_oval(215, 0, 260, 45, fill=color, outline=color)
            btn.create_rectangle(22, 0, 238, 45, fill=color, outline=color)
            btn.create_text(130, 22, text="Forgot Password",
                            font=("Poppins", 13, "bold"), fill="black")

        _draw_btn("#F3D58D")
        btn.bind("<Enter>",    lambda e: _draw_btn(PRIMARY_HOVER))
        btn.bind("<Leave>",    lambda e: _draw_btn("#F3D58D"))
        btn.bind("<Button-1>", lambda e: self._submit())

        # back link
        back_lbl = tk.Label(card, text="← Back to log in",
                            font=("Poppins", 9), fg=PRIMARY,
                            bg="white", cursor="hand2")
        back_lbl.pack(pady=(4, 0))
        back_lbl.bind("<Button-1>", lambda e: self._on_back())
        back_lbl.bind("<Enter>",    lambda e: back_lbl.config(fg=PRIMARY_HOVER))
        back_lbl.bind("<Leave>",    lambda e: back_lbl.config(fg=PRIMARY))

    # ── actions ───────────────────────────────────────────────────────
    def _clear_messages(self):
        self._error_lbl.config(text="")
        self._success_lbl.config(text="")
        self._entry.config(highlightthickness=0)

    def _submit(self):
        identifier = self._entry.get().strip()
        if not identifier:
            self._error_lbl.config(
                text="Please enter your username or email before continuing.")
            self._entry.config(highlightbackground=ERROR_CLR, highlightthickness=1)
            return

        self._clear_messages()
        # show sending state
        self._success_lbl.config(text="Sending… please wait.", fg="#E59E2C")
        self.update()

        import threading

        def _send():
            try:
                email = request_password_reset(identifier)
                # update UI on main thread
                def _done():
                    self._entry.delete(0, "end")
                    self._success_lbl.config(
                        fg=SUCCESS_CLR,
                        text="If this account exists, reset instructions have been "
                             f"sent to the registered email"
                             f"{(' (' + email + ')') if email else ''}.")
                self.after(0, _done)
            except Exception as ex:
                def _err():
                    self._success_lbl.config(text="")
                    self._error_lbl.config(text=f"Error: {str(ex)[:80]}")
                self.after(0, _err)

        threading.Thread(target=_send, daemon=True).start()
