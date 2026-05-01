import tkinter as tk
from werkzeug.security import check_password_hash

from constants import (
    BG, WHITE, CREAM, AMBER, AMBER_LIGHT,
    TEXT_DARK, TEXT_MUTE, TEXT_GRAY, RED_ERR,
    supabase, load_icon
)


class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_success):
        """
        parent     : parent Tk window
        on_success : callback(org_dict) called after successful login
        """
        super().__init__(parent)
        self.on_success = on_success
        self.title("PockiTrack | Login")
        self.geometry("460x520")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()
        self._build()

    def _build(self):
        # ── logo top-left ──
        logo_row = tk.Frame(self, bg=BG)
        logo_row.place(x=14, y=14)
        self._set_logo(logo_row)

        # ── white login box ──
        box = tk.Frame(self, bg=WHITE, bd=0,
                       highlightbackground="#E0E0E0", highlightthickness=1)
        box.place(relx=0.5, rely=0.52, anchor="center", width=390, height=400)

        tk.Label(box, text="Log in", bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 22, "bold")).pack(pady=(30, 4))
        tk.Label(box, text="Enter your details to sign in to your account.",
                 bg=WHITE, fg=TEXT_GRAY, font=("Poppins", 10)).pack(pady=(0, 20))

        form = tk.Frame(box, bg=WHITE)
        form.pack(padx=40, fill="x")

        # Username
        tk.Label(form, text="Username", bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 9)).pack(anchor="w")
        self.username_var = tk.StringVar()
        un_entry = tk.Entry(form, textvariable=self.username_var,
                            font=("Poppins", 11), relief="flat",
                            highlightbackground=CREAM, highlightthickness=1)
        un_entry.pack(fill="x", ipady=6, pady=(2, 12))
        un_entry.bind("<FocusIn>",  lambda e: un_entry.config(highlightbackground=AMBER))
        un_entry.bind("<FocusOut>", lambda e: un_entry.config(highlightbackground=CREAM))

        # Password
        tk.Label(form, text="Password", bg=WHITE, fg=TEXT_DARK,
                 font=("Poppins", 9)).pack(anchor="w")
        pw_row = tk.Frame(form, bg=WHITE,
                          highlightbackground=CREAM, highlightthickness=1)
        pw_row.pack(fill="x", pady=(2, 8))
        self.pw_var = tk.StringVar()
        pw_entry = tk.Entry(pw_row, textvariable=self.pw_var,
                            show="*", font=("Poppins", 11), relief="flat", bd=0)
        pw_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(6, 0))
        pw_entry.bind("<FocusIn>",  lambda e: pw_row.config(highlightbackground=AMBER))
        pw_entry.bind("<FocusOut>", lambda e: pw_row.config(highlightbackground=CREAM))

        self.show_pw = False

        def toggle_pw():
            self.show_pw = not self.show_pw
            pw_entry.config(show="" if self.show_pw else "*")
            eye_btn.config(text="🙈" if self.show_pw else "👁")

        eye_btn = tk.Button(pw_row, text="👁", font=("Poppins", 10),
                            bg=WHITE, relief="flat", cursor="hand2", command=toggle_pw)
        eye_btn.pack(side="right", padx=4)

        tk.Label(form, text="Forgot password?", bg=WHITE, fg="#A24A00",
                 font=("Poppins", 9), cursor="hand2").pack(anchor="e", pady=(0, 4))

        self.err_label = tk.Label(box, text="", bg=WHITE, fg=RED_ERR,
                                  font=("Poppins", 9))
        self.err_label.pack()

        login_btn = tk.Button(box, text="Log in", command=self._login,
                              bg=AMBER_LIGHT, fg=TEXT_DARK,
                              font=("Poppins", 13, "bold"),
                              relief="flat", cursor="hand2", bd=1,
                              activebackground=AMBER, activeforeground=WHITE)
        login_btn.pack(padx=40, fill="x", ipady=6, pady=16)
        self.bind("<Return>", lambda e: self._login())

    def _set_logo(self, parent):
        logo_img = load_icon("pocki_logo.png", (40, 40))
        if logo_img:
            lbl = tk.Label(parent, image=logo_img, bg=BG)
            lbl.image = logo_img
            lbl.pack(side="left")
        tk.Label(parent, text="PockiTrack", bg=BG, fg=TEXT_DARK,
                 font=("Poppins", 16, "bold")).pack(side="left", padx=6)

    def _login(self):
        username = self.username_var.get().strip()
        password = self.pw_var.get().strip()

        if not username or not password:
            self.err_label.config(text="Please enter username and password.")
            return

        self.err_label.config(text="Logging in…", fg=TEXT_MUTE)
        self.update_idletasks()

        try:
            result = supabase.table("organizations").select("*") \
                             .eq("username", username).execute()

            if not result.data:
                self.err_label.config(text="Organization not found.", fg=RED_ERR)
                return

            org = result.data[0]

            if org.get("status") == "Archived":
                self.err_label.config(
                    text="This account is archived. Contact OSAS.", fg=RED_ERR)
                return

            stored_hash = org.get("password", "")
            if not stored_hash:
                self.err_label.config(text="No password set for this account.", fg=RED_ERR)
                return

            if not check_password_hash(stored_hash, password):
                self.err_label.config(text="Incorrect password.", fg=RED_ERR)
                return

            self.destroy()
            self.on_success(org)

        except Exception as e:
            self.err_label.config(text=f"Connection error: {str(e)[:55]}", fg=RED_ERR)