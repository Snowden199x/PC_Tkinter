import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
"""
profile_screen.py – Organisation profile / settings
"""
import tkinter as tk
from constants import *
from widgets import StyledEntry, RoundedButton
import os
from PIL import Image, ImageTk


class ProfileScreen(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CREAM, **kwargs)
        self._avatar_img = None
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_CREAM, padx=28, pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Profile", bg=BG_CREAM,
                 fg=TEXT_DARK, font=font(18, "bold")).pack(anchor="w")

        # ── Card ──────────────────────────────────────────────────────
        card = tk.Frame(self, bg=BG_WHITE, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        # ── Avatar ────────────────────────────────────────────────────
        avatar_col = tk.Frame(card, bg=BG_WHITE)
        avatar_col.pack(side="left", anchor="n", padx=(0, 30))

        self._canvas = tk.Canvas(avatar_col, width=90, height=90,
                                 bg=BG_WHITE, bd=0, highlightthickness=0)
        self._canvas.pack()
        self._draw_avatar()

        RoundedButton(avatar_col, text="Change Photo",
                      bg=AMBER, fg="white",
                      command=self._change_photo,
                      width=100, height=30,
                      radius=8, font_size=8).pack(pady=6)

        # ── Form ──────────────────────────────────────────────────────
        form = tk.Frame(card, bg=BG_WHITE)
        form.pack(side="left", fill="both", expand=True)

        tk.Label(form, text="Organization Information",
                 bg=BG_WHITE, fg=TEXT_DARK,
                 font=font(12, "bold")).pack(anchor="w", pady=(0, 14))

        fields = [
            ("Organization Name",       "Information Technology Inks, Nab."),
            ("Organization Short Name", "ITI"),
            ("Department",              "College of Computer Studies"),
            ("Alias",                   "ITI"),
            ("School / University",
             "Laguna State Polytechnic University – Sta. Cruz Campus"),
        ]

        # two-column grid for first four fields
        grid = tk.Frame(form, bg=BG_WHITE)
        grid.pack(fill="x", pady=(0, 10))
        for i, (label, default) in enumerate(fields[:4]):
            col = i % 2
            row = i // 2
            lf = tk.Frame(grid, bg=BG_WHITE)
            lf.grid(row=row, column=col, padx=(0 if col == 0 else 10, 0),
                    pady=4, sticky="nsew")
            grid.columnconfigure(col, weight=1)
            tk.Label(lf, text=label, bg=BG_WHITE,
                     fg=TEXT_LABEL, font=font(8, "bold"),
                     anchor="w").pack(fill="x")
            e = StyledEntry(lf, placeholder=default)
            e.entry.delete(0, "end")
            e.entry.insert(0, default)
            e.entry.config(fg=TEXT_DARK, show="")
            e.pack(fill="x")

        # last field full width
        lf = tk.Frame(form, bg=BG_WHITE)
        lf.pack(fill="x", pady=4)
        tk.Label(lf, text=fields[4][0], bg=BG_WHITE,
                 fg=TEXT_LABEL, font=font(8, "bold"),
                 anchor="w").pack(fill="x")
        e = StyledEntry(lf, placeholder=fields[4][1])
        e.entry.delete(0, "end")
        e.entry.insert(0, fields[4][1])
        e.entry.config(fg=TEXT_DARK, show="")
        e.pack(fill="x")

        # Save button
        RoundedButton(form, text="Save Changes",
                      bg=PRIMARY, fg="white",
                      width=150, height=38,
                      radius=10).pack(anchor="e", pady=14)

    def _draw_avatar(self):
        self._canvas.delete("all")
        if self._avatar_img:
            self._canvas.create_image(45, 45, image=self._avatar_img)
        else:
            # grey circle placeholder
            self._canvas.create_oval(5, 5, 85, 85,
                                     fill="#D0C8BE", outline="")
            self._canvas.create_text(45, 45, text="👤",
                                     font=font(28), fill=TEXT_MUTED)

    def _change_photo(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path:
            try:
                img = Image.open(path).resize((80, 80), Image.LANCZOS)
                self._avatar_img = ImageTk.PhotoImage(img)
                self._draw_avatar()
            except Exception:
                pass
