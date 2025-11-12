# app_alpha.py
"""
Projekt: Focus Pet – fookustaimer koos kasvava kassiga
Autorid: Maria Elisa Vassiljeva, Viktorija Korjagina
Eeskujud/Allikad:
  - PEP 8 (koodistiil): https://peps.python.org/pep-0008/
  - PEP 257 (docstring’id): https://peps.python.org/pep-0257/
  - Tkinter, Pillow dokumentatsioonid

Kirjeldus:
  Lihtne Tkinteri rakendus, mis võimaldab teha fookussessioone (Pomodoro-stiilis),
  teenida punkte ning “kasvatada” kassi. Pildid on ette renderdatud stseenid
  (taust+loom), mida valitakse taseme ja tuju järgi.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

# ----- Kaustade ja failide teed -----
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"
PROGRESS_PATH = DATA / "progress.json"

# ----- Taimeri valikud -----
FOCUS_CHOICES = [0.1, 5, 10, 15, 20, 25, 30]  # minutites (0.1 testimiseks)
SESSIONS_CHOICES = [1, 2, 3]  # mitu fookussessiooni järjest
BREAK_CHOICES = [0.1, 3, 5, 7, 10]  # paus minutites
POINTS_PER_MINUTE = 1  # mitu punkti iga minuti eest

# Tase kasvab, kui saavutatakse järgmised punktid (praegu 0.1 ja 0.2 testiks)
GROW_THRESHOLDS: Dict[str, float] = {
    "baby": 0.1,  # hiljem nt 180
    "teen": 0.2,  # hiljem nt 360
}

# Pildid (taust ja kass koos)
STAGES = ("baby", "teen", "adult")
MOODS = ("sad", "neutral", "happy")
SCENES: Dict[str, Dict[str, str]] = {
    "baby": {"sad": "cat2.png", "neutral": "cat1.png", "happy": "cat3.png"},
    "teen": {"sad": "cat5.png", "neutral": "cat4.png", "happy": "cat6.png"},
    "adult": {"sad": "cat13.png", "neutral": "cat10.png", "happy": "cat12.png"},
}


# Abifunktsioonid
def format_mmss(seconds: float) -> str:
    """Kujundab sekundid kujule MM:SS."""
    s_int = max(0, int(round(seconds)))
    minutes, secs = divmod(s_int, 60)
    return f"{minutes:02d}:{secs:02d}"


def load_photo_fit(path: Path, max_w: int, max_h: int) -> Optional[ImageTk.PhotoImage]:
    """
    Avab pildi ja vähendab/suurendab seda antud piiridesse sobivaks.

    :param path: Pildi failitee.
    :param max_w: Maksimaalne laius pikslites.
    :param max_h: Maksimaalne kõrgus pikslites.
    :return: ImageTk.PhotoImage või None, kui avamine ebaõnnestus.
    """
    try:
        img = Image.open(path).convert("RGBA")
    except Exception:
        return None

    width, height = img.size
    if max_w <= 0 or max_h <= 0:
        return ImageTk.PhotoImage(img)

    scale = min(max_w / width, max_h / height)
    new_w = max(1, int(width * scale))
    new_h = max(1, int(height * scale))

    if (new_w, new_h) != (width, height):
        img = img.resize((new_w, new_h), Image.LANCZOS)

    return ImageTk.PhotoImage(img)


#  Progresseerumise andmete lugemine/salvestamine
def load_progress() -> Dict[str, object]:
    """
    Loeb JSON-failist kassi seisu (punktid, tase, tuju). Kui puudub, loob uue.

    :return: Sõnastik võtmetega: total, stage, mood, last_session.
    """
    defaults: Dict[str, object] = {
        "total": 0.0,
        "stage": "baby",
        "mood": "sad",
        "last_session": None,
    }

    try:
        raw = PROGRESS_PATH.read_text(encoding="utf-8") if PROGRESS_PATH.exists() else "{}"
        data = json.loads(raw or "{}")
    except Exception:
        data = {}

    progress: Dict[str, object] = {**defaults, **data}

    try:
        progress["total"] = float(progress["total"])  # type: ignore[assignment]
    except Exception:
        progress["total"] = 0.0

    if progress["stage"] not in STAGES:
        progress["stage"] = "baby"
    if progress["mood"] not in MOODS:
        progress["mood"] = "sad"

    save_progress(progress)
    return progress


def save_progress(progress: Dict[str, object]) -> None:
    """Salvestab kassi seisu progress.json-faili."""
    PROGRESS_PATH.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# Rakenduse põhiklass
class App:
    """Focus Pet rakendus – fookustaimer koos visuaalse tagasisidega."""

    def __init__(self, root: tk.Tk):
        """Initsialiseerib GUI, laeb seisu ja seab sündmused."""
        # Aken
        self.root = root
        root.title("Focus Pet (alpha)")
        root.geometry("1100x720")
        root.minsize(900, 600)

        # Kassi ja taimeri olek
        self.progress = load_progress()
        self.state = "idle"  # idle | focusing | break
        self.end_ts: Optional[float] = None
        self.focus_len_min = 25.0
        self.break_len_min = 5.0
        self.total_cycles = 3
        self.current_cycle = 0
        self._img_cache: Optional[ImageTk.PhotoImage] = None

        # Paigutus: vasakul paneel, paremal pilt
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        # VASAK PANEEL (valikud ja punktid)
        left = ttk.Frame(root, padding=12)
        left.grid(row=0, column=0, rowspan=3, sticky="nsw")

        ttk.Label(left, text="Focus (min)").grid(row=0, column=0, sticky="w")
        self.focus_cb = ttk.Combobox(
            left, width=6, state="readonly", values=[str(x) for x in FOCUS_CHOICES]
        )
        self.focus_cb.set("25")
        self.focus_cb.grid(row=1, column=0, sticky="w", pady=(0, 8))

        ttk.Label(left, text="Sessions").grid(row=2, column=0, sticky="w")
        self.sessions_cb = ttk.Combobox(
            left, width=6, state="readonly", values=[str(x) for x in SESSIONS_CHOICES]
        )
        self.sessions_cb.set("3")
        self.sessions_cb.grid(row=3, column=0, sticky="w", pady=(0, 8))

        ttk.Label(left, text="Break (min)").grid(row=4, column=0, sticky="w")
        self.break_cb = ttk.Combobox(
            left, width=6, state="readonly", values=[str(x) for x in BREAK_CHOICES]
        )
        self.break_cb.set("5")
        self.break_cb.grid(row=5, column=0, sticky="w", pady=(0, 12))

        self.points_lbl = ttk.Label(
            left, text=f"Points: {float(self.progress['total']):.1f}"
        )
        self.points_lbl.grid(row=6, column=0, sticky="w", pady=(0, 6))

        self.status_lbl = ttk.Label(
            left, text="Ready to start", foreground="#2e7d32", wraplength=220
        )
        self.status_lbl.grid(row=7, column=0, sticky="w")

        # ÜLEMINE OSA: taimer
        self.timer_lbl = ttk.Label(root, text="00:00", font=("Consolas", 28, "bold"))
        self.timer_lbl.grid(row=0, column=1, sticky="ne", padx=12, pady=12)

        # KESKMINE OSA: pilt
        self.scene_lbl = ttk.Label(root)
        self.scene_lbl.grid(row=1, column=1, sticky="nsew")
        self.scene_lbl.bind("<Configure>", lambda _e: self._render_scene())

        # ALUMINE OSA: nupud
        btns = ttk.Frame(root)
        btns.grid(row=2, column=1, sticky="e", padx=12, pady=12)
        ttk.Button(btns, text="▶ START", command=self.on_start, width=12).grid(
            row=0, column=0, padx=6
        )
        ttk.Button(btns, text="⏸ PAUSE", command=self.on_pause, width=12).grid(
            row=0, column=1, padx=6
        )
        ttk.Button(btns, text="⏹ STOP", command=self.on_stop, width=12).grid(
            row=0, column=2, padx=6
        )

        # Esmane joonistus ja taimeri käivitamine
        self._render_scene()
        self.root.after(200, self._tick)

    # Nuppude funktsioonid
    def on_start(self) -> None:
        """Käivitab uue fookussessiooni või jätkab pärast pausi."""
        if self.state not in ("idle", "break"):
            return

        try:
            self.focus_len_min = float(self.focus_cb.get())
        except Exception:
            self.focus_len_min = 25.0

        try:
            self.total_cycles = int(self.sessions_cb.get())
        except Exception:
            self.total_cycles = 3

        try:
            self.break_len_min = float(self.break_cb.get())
        except Exception:
            self.break_len_min = 5.0

        if self.state == "idle":
            self.current_cycle = 1

        self.state = "focusing"
        self.end_ts = time.time() + self.focus_len_min * 60
        self.status_lbl.configure(
            text=f"Session {self.current_cycle}/{self.total_cycles} started!",
            foreground="#2e7d32",
        )
        self.timer_lbl.configure(text=format_mmss(self.end_ts - time.time()))

        if self.progress["mood"] == "sad":
            self.progress["mood"] = "neutral"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

    def on_pause(self) -> None:
        """Peatab taimeri (ajutiselt)."""
        if self.state in ("focusing", "break") and self.end_ts:
            left = max(0.0, self.end_ts - time.time())
            self.state = "idle"
            self.end_ts = None
            self.timer_lbl.configure(text=format_mmss(left))
            self.progress["mood"] = "sad"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()
            self.status_lbl.configure(
                text="Paused. Press START to resume.", foreground="#b26a00"
            )

    def on_stop(self) -> None:
        """Tühistab sessiooni täielikult."""
        if self.state in ("focusing", "break"):
            self.state = "idle"
            self.end_ts = None
            self.current_cycle = 0
            self.timer_lbl.configure(text="00:00")
            self.progress["mood"] = "sad"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()
            self.status_lbl.configure(
                text="Session cancelled — no points added.", foreground="#e53935"
            )

    # Taimeri tsükkel
    def _tick(self) -> None:
        """Uuendab taimerit iga 200 ms järel ja vahetab olekuid piirhetkedel."""
        now = time.time()

        if self.state in ("focusing", "break") and self.end_ts:
            left = self.end_ts - now
            self.timer_lbl.configure(text=format_mmss(max(0.0, left)))

            # Kui aeg saab läbi
            if left <= 0:
                if self.state == "focusing":
                    gained = self.focus_len_min * POINTS_PER_MINUTE
                    self.progress["total"] = float(self.progress["total"]) + gained
                    self.progress["last_session"] = datetime.now().isoformat(
                        timespec="seconds"
                    )
                    save_progress(self.progress)  # type: ignore[arg-type]
                    self.points_lbl.configure(
                        text=f"Points: {float(self.progress['total']):.1f}"
                    )
                    self._grow_stage_if_needed()

                    # Kass on rõõmus
                    self.progress["mood"] = "happy"
                    save_progress(self.progress)  # type: ignore[arg-type]
                    self._render_scene()

                    if self.current_cycle < self.total_cycles:
                        # läheb pausile
                        self.state = "break"
                        self.end_ts = time.time() + self.break_len_min * 60
                        self.status_lbl.configure(
                            text=(
                                f"Session {self.current_cycle} finished "
                                f"(+{gained:.1f}). Break {self.break_len_min:g} min"
                            ),
                            foreground="#866a24",
                        )
                    else:
                        # kõik sessioonid tehtud
                        self.state = "idle"
                        self.end_ts = None
                        self.timer_lbl.configure(text="00:00")
                        self.status_lbl.configure(
                            text=f"All {self.total_cycles} sessions done! (+{gained:.1f})",
                            foreground="#866a24",
                        )
                        self._grow_stage_if_needed()
                        self.progress["mood"] = "happy"
                        save_progress(self.progress)  # type: ignore[arg-type]
                        self._render_scene()

                else:
                    # paus lõppes → uus fookus
                    self.current_cycle += 1
                    self.state = "focusing"
                    self.end_ts = time.time() + self.focus_len_min * 60
                    self.status_lbl.configure(
                        text=f"Session {self.current_cycle}/{self.total_cycles} started!",
                        foreground="#866a24",
                    )
                    self.progress["mood"] = "neutral"
                    save_progress(self.progress)  # type: ignore[arg-type]
                    self._render_scene()

        # korduskutse iga 0.2 sekundi järel
        self.root.after(200, self._tick)

    # Tase kasvab
    def _grow_stage_if_needed(self) -> None:
        """Kontrollib, kas punktid on piisavad järgmisele tasemele liikumiseks."""
        stage = str(self.progress.get("stage", "baby"))
        total = float(self.progress.get("total", 0.0))

        if stage == "baby" and total >= GROW_THRESHOLDS["baby"]:
            self.progress["stage"] = "teen"
        elif stage == "teen" and total >= GROW_THRESHOLDS["teen"]:
            self.progress["stage"] = "adult"

        save_progress(self.progress)  # type: ignore[arg-type]

    # Pildi joonistamine
    def _current_image_path(self) -> Path:
        """Tagastab pildi tee (tase + tuju) järgi."""
        stage = str(self.progress.get("stage", "baby"))
        mood = str(self.progress.get("mood", "sad"))
        return ASSETS / SCENES[stage][mood]

    def _render_scene(self) -> None:
        """Laeb ja kuvab pildi aknas sobivas suuruses."""
        image_path = self._current_image_path()
        width = self.scene_lbl.winfo_width() or 900
        height = self.scene_lbl.winfo_height() or 600

        if not image_path.exists():
            self.scene_lbl.configure(text=f"Image not found:\n{image_path.name}")
            return

        photo = load_photo_fit(image_path, width, height)
        if photo is None:
            messagebox.showwarning("Error", f"Could not open image: {image_path.name}")
            return

        self._img_cache = photo
        self.scene_lbl.configure(image=self._img_cache, text="")


# Käivitamine
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
