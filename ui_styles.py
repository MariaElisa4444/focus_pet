# ui_styles.py
# Siin failis on kõik värvid, fondid ja seaded ühes kohas

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

def make_toast(parent: tk.Widget) -> tuple[tk.Frame, tk.Label]:
    """
    Loob toast-teate UI (frame + label).
    Tagastab (toast_frame, toast_label).
    """
    toast_frame = tk.Frame(parent, bg="#D1CCC1", bd=1, relief="solid")
    toast_lbl = tk.Label(
        toast_frame,
        text="",
        font=("Bernoru SemiCondensed", 18, "bold"),
        bg="#D1CCC1",
        fg="#000000",
        padx=18,
        pady=10,
    )
    toast_lbl.pack()
    toast_frame.place_forget()  # alguses peidetud
    return toast_frame, toast_lbl

def make_control_buttons(
    parent: tk.Widget,
    on_start,
    on_pause,
    on_stop,
) -> tuple[tk.Button, tk.Button, tk.Button]:
    """
    Loob START/PAUSE/STOP nupud ühesuguse stiiliga ja paigutusega.
    Tagastab (start_btn, pause_btn, stop_btn).
    """
    button_font = FONT_BOTTOM_BTNS

    start_btn = tk.Button(parent, text="START", font=button_font, fg="black", bd=0, relief="flat", command=on_start)
    pause_btn = tk.Button(parent, text="PAUSE", font=button_font, fg="black", bd=0, relief="flat", command=on_pause)
    stop_btn  = tk.Button(parent, text="STOP",  font=button_font, fg="black", bd=0, relief="flat", command=on_stop)

    style_control_button(start_btn)
    style_control_button(pause_btn)
    style_control_button(stop_btn)

    start_btn.grid(row=0, column=0, padx=10)
    pause_btn.grid(row=0, column=1, padx=10)
    stop_btn.grid(row=0, column=2, padx=10)

    return start_btn, pause_btn, stop_btn

def make_hud_label(parent: tk.Widget) -> tk.Label:
    """Loob HUD labeli ja rakendab stiilid."""
    lbl = tk.Label(parent, text="")
    style_hud_label(lbl)
    return lbl
