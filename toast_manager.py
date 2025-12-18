# toast_manager.py
# Selles failis on ToastManager, mis haldab ajutisi teateid (toast).

from __future__ import annotations
import tkinter as tk


class ToastManager:
    """Vastutab toast-teate näitamise ja automaatse peitmise eest."""

    def __init__(self, root: tk.Tk, frame: tk.Frame, label: tk.Label):
        """
        :param root: Tk juuraken (vajalik after() jaoks)
        :param frame: Toasti raam (Frame), mida näidatakse/peidetakse
        :param label: Toasti tekstilabel (Label), kuhu paneme sõnumi
        """
        self.root = root
        self.frame = frame
        self.label = label
        self._after_id = None  # after() id, et saaks cancel'ida

    def show(self, text: str, kind: str = "info", ms: int = 2500) -> None:
        """
        Näitab toast teadet.
        kind: info | error
        ms: kui kaua teade ekraanil püsib (millisekundites)
        """
        colors = {
            "info":  ("#D1CCC1", "#261710"),
            "error": ("#D1CCC1", "#6D0C0C"),
        }
        bg, fg = colors.get(kind, colors["info"])

        # Uuendame stiili ja teksti
        self.frame.configure(bg=bg)
        self.label.configure(text=text, bg=bg, fg=fg)

        # Näitame toast-i kindlas kohas
        self.frame.place(relx=0.525, rely=0.08, anchor="center")

        # Kui eelmine toast oli aktiivne, cancel'ime selle
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass

        # Paneme uue auto-hide
        self._after_id = self.root.after(ms, self.hide)

    def hide(self) -> None:
        """Peidab toast teate."""
        self.frame.place_forget()
        self._after_id = None
