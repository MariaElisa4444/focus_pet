# ui_styles.py
# Siin failis on KÕIK värvid, fondid ja seaded ühes kohas

import tkinter as tk

# Üldised värvid
COLOR_BTN_BG = "#D1CCC1"
COLOR_BTN_ACTIVE = "#B7B3A9"
COLOR_BTN_TEXT = "black"

COLOR_BOTTOM_BAR_BG = "#643F2C"
COLOR_TIMER_BG = "#FFF3CD"
COLOR_TIMER_TEXT = "#000000"
COLOR_HUD_TEXT = "#3B2A21"

COLOR_SPLASH_BTN_BG = "#D1CCC1"
COLOR_SPLASH_BTN_ACTIVE = "#B7B3A9"
COLOR_SPLASH_TEXT = "#000000"

# Fondid
FONT_SPLASH_BTN = ("Bernoru SemiCondensed", 30, "bold")
FONT_BOTTOM_BTNS = ("Bernoru SemiCondensed", 18, "bold")
FONT_TIMER = ("Bernoru SemiCondensed", 50, "bold")
FONT_HUD = ("Bernoru SemiCondensed", 20, "bold")

def style_splash_start_button(btn: tk.Button) -> None:
    """Paneme START nupule ühtsed stiilid."""
    btn.configure(
        font=FONT_SPLASH_BTN,
        fg=COLOR_SPLASH_TEXT,
        bg=COLOR_SPLASH_BTN_BG,
        activeforeground=COLOR_SPLASH_TEXT,
        activebackground=COLOR_SPLASH_BTN_ACTIVE,
        bd=0,
        highlightthickness=0,
        relief="flat",
        cursor="hand2",
    )

def style_control_button(btn: tk.Button) -> None:
    """Paneme START/PAUSE/STOP nupule ühtsed stiilid."""
    btn.configure(
        font=FONT_BOTTOM_BTNS,
        bg=COLOR_BTN_BG,
        fg=COLOR_BTN_TEXT,
        activebackground=COLOR_BTN_ACTIVE,
        activeforeground=COLOR_BTN_TEXT,
        bd=0,
        relief="flat",
        padx=20,
        pady=10,
        cursor="hand2",
    )

def style_hud_label(lbl: tk.Label) -> None:
    """HUD stiilid. Näitab focus/break/pause olekut ekraani nurgas."""
    lbl.configure(
        bg=COLOR_TIMER_BG,
        fg=COLOR_HUD_TEXT,
        font=FONT_HUD,
        bd=0,
        relief="flat",
        padx=5,
        pady=5,
        highlightthickness=0,
    )

def make_bottom_bar(parent: tk.Widget) -> tk.Frame:
    """Loome alumise nupu riba (taustavärv ja raam)."""
    return tk.Frame(parent, bg=COLOR_BOTTOM_BAR_BG)

def make_timer_label(parent: tk.Widget) -> tk.Label:
    """Loome taimeri labeli paremas ülanurgas (taust ja font)."""
    return tk.Label(
        parent,
        text="00:00",
        font=FONT_TIMER,
        bg=COLOR_TIMER_BG,
        fg=COLOR_TIMER_TEXT,
        bd=0,
        padx=14,
        pady=4,
    )
