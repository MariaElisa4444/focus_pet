"""
Projekt: Focus Pet – fookustaimer koos kasvava kassiga
Autorid: Maria Elisa Vassiljeva, Viktorija Korjagina
Käivitamisjuhend:
    1. Laadi alla projekti ZIP fail ja paki see lahti
    2. Veendu, et Python 3.10+ on installitud
    3. Ava terminal ja paigalda vajalikud teegid: pip install pillow
    4. Liigu kaustasse, kuhu programm on salvestatud: cd (programmi kausta tee)
    5. Käivita programm: python focus_pet_alpha.py
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

from menu_panel import SideMenu  # meie eraldi failis olev külgmenüü
import ui_styles  # kujundus (värvid, fondid, nupu stiilid) on eraldi failis

# Muusika jaoks kasutame pygame.mixer teeki
# (kui pygame pole installitud, muusika lihtsalt ei tööta, aga programm töötab edasi)
try:
    import pygame  # type: ignore
except Exception:
    pygame = None  # type: ignore

from music_player import MusicPlayer  # muusika loogika on eraldi failis

# Kaustade ja failide teed
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"
PROGRESS_PATH = DATA / "progress.json"

# Taimeri valikud
FOCUS_CHOICES = [0.1, 5, 10, 15, 20, 25, 30]               # minutites (0.1 testimiseks)
SESSIONS_CHOICES = [1, 2, 3]                               # mitu fookussessiooni järjest
BREAK_CHOICES = [0.1, 3, 5, 7, 10]                         # paus minutites
POINTS_PER_MINUTE = 1                                      # mitu punkti iga minuti eest

# Stardi ekraani seaded
START_SCREEN_FILE = "focuspet_start.png"                   # pilt assets kaustas
START_BUTTON_FONT = ("Bernoru SemiCondensed", 30, "bold")
START_BUTTON_TEXT_COLOR = "#000000"                      # must tekst

# Tase kasvab, kui saavutatakse järgmised punktid (praegu 0.1 ja 0.2 testiks)
GROW_THRESHOLDS: Dict[str, float] = {
    "baby": 0.1,                             # hiljem nt 180
    "teen": 0.2,                             # hiljem nt 360
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
    Avab pildi ja paneb ta akna peale nii, et tühi ruum ei jääks.
    Pildi proportsioon jääb samaks ja üle ääre osa lõigatakse keskelt ära.

    :param path: Pildi failitee
    :param max_w: Ala laius pikslites
    :param max_h: Ala kõrgus pikslites
    :return: ImageTk.PhotoImage või None, kui avamine ebaõnnestus
    """
    try:
        img = Image.open(path).convert("RGBA")
    except Exception:
        return None

    width, height = img.size
    if max_w <= 0 or max_h <= 0:
        return ImageTk.PhotoImage(img)

    # Kasutame max, et pilt KATAB ala (mitte lihtsalt mahub)
    scale = max(max_w / width, max_h / height)
    new_w = max(1, int(width * scale))
    new_h = max(1, int(height * scale))

    if (new_w, new_h) != (width, height):
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # Lõikame keskelt sobivaks suuruseks
    if new_w > max_w or new_h > max_h:
        left = max(0, (new_w - max_w) // 2)
        top = max(0, (new_h - max_h) // 2)
        right = left + max_w
        bottom = top + max_h
        img = img.crop((left, top, right, bottom))

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
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        # Pildid hoian muutujas, et Python neid prügikasti ei viskaks
        self._img_cache: Optional[ImageTk.PhotoImage] = None
        self._splash_img_cache: Optional[ImageTk.PhotoImage] = None

        # Kassi ja taimeri olek
        self.progress = load_progress()
        self.state = "idle"  # idle | focusing | break
        self.end_ts: Optional[float] = None
        self.paused_left: float | None = None  # mitu sekundit on pausil alles
        self.focus_len_min = 25.0
        self.break_len_min = 5.0
        self.total_cycles = 3
        self.current_cycle = 0

        # Muusika
        self.music = MusicPlayer(assets_path=ASSETS, pygame_module=pygame)

        # Kaks erinevat ekraani: stardi ekraan ja põhi ekraan
        self.splash_frame = tk.Frame(root, bg="#fbe7b3")
        self.splash_frame.grid(row=0, column=0, sticky="nsew")

        self.main_frame = tk.Frame(root, bg="#f5f5f5")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_remove()  # alguses peidame põhi ekraani

        # Loome mõlema ekraani kasutajaliidese
        self._build_splash_ui()
        self._build_main_ui()

        # Käivitame taimeri tsükli
        self.root.after(200, self._tick)

    # Stardi ekraan (splash)

    def _build_splash_ui(self) -> None:
        """Loob stardi ekraani pildi ja START nupu."""

        # Label, kuhu paneme suure taustapildi
        self.splash_img_label = ttk.Label(self.splash_frame)
        self.splash_img_label.place(
            relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0
        )

        # Kui aken muudab suurust, joonistame pildi uuesti
        self.splash_frame.bind("<Configure>", lambda _e: self._render_splash())

        # START nupp
        # Siin on ainult loogika (text + command), stiili paneme ui_styles fail
        self.splash_start_btn = tk.Button(
            self.splash_frame,
            text="START",  # nupu tekst
            command=self._on_splash_start_clicked,
        )

        # nupu tekst / font / värv jne (must tekst)
        ui_styles.style_splash_start_button(self.splash_start_btn)

        self.splash_start_btn.place(
            relx=0.5,
            rely=0.635,
            anchor="center",
            width=240,
            height=78,
        )

    def _render_splash(self) -> None:
        """Joonistab stardi ekraani pildi vastavalt akna suurusele."""
        image_path = ASSETS / START_SCREEN_FILE
        width = self.splash_frame.winfo_width() or 1100
        height = self.splash_frame.winfo_height() or 720

        if not image_path.exists():
            # kui pilti pole, näitame lihtsat teksti
            self.splash_img_label.configure(
                text=f"Missing: {image_path.name}", anchor="center"
            )
            return

        photo = load_photo_fit(image_path, width, height)
        if photo is None:
            self.splash_img_label.configure(
                text=f"Cannot open: {image_path.name}", anchor="center"
            )
            return

        self._splash_img_cache = photo
        self.splash_img_label.configure(image=self._splash_img_cache, text="")

    def _on_splash_start_clicked(self):
        """Kui vajutame START stardi ekraanil, peidame splash ja näitame main UI."""
        self.splash_frame.grid_remove()  # peidame stardi ekraani
        self.main_frame.grid()           # toome välja põhivaate

    #  Põhi ekraan

    def _build_main_ui(self) -> None:
        """Loob põhi ekraani: kassi pilt, taimer, nupud ja külgmenüü."""
        mf = self.main_frame

        # kassipildi label, võtab kogu ala
        mf.columnconfigure(0, weight=1)
        mf.rowconfigure(0, weight=1)

        self.scene_lbl = ttk.Label(mf)
        self.scene_lbl.grid(row=0, column=0, sticky="nsew")
        # kui suurus muutub, sobitame pildi akna järgi
        self.scene_lbl.bind("<Configure>", lambda _e: self._render_scene())

        # Külgmenüü (SideMenu), väljatõmmatav paneel
        self.menu = SideMenu(
            parent=mf,
            assets_path=ASSETS,
            focus_choices=FOCUS_CHOICES,
            sessions_choices=SESSIONS_CHOICES,
            break_choices=BREAK_CHOICES,
            initial_points=float(self.progress["total"]),
            on_update_scene=self._render_scene,
            on_music_toggle=self._on_music_toggle,
        )

        # Seome comboboxid ja sildid nii, et ülejäänud kood ei muutuks
        self.focus_cb = self.menu.focus_cb
        self.sessions_cb = self.menu.sessions_cb
        self.break_cb = self.menu.break_cb
        self.points_lbl = self.menu.points_label
        self.status_lbl = self.menu.status_label

        # Taimer paremas ülanurgas (pildi peal)
        # Kasutame tk.Label, et saaksime taustavärvi panna
        self.timer_lbl = ui_styles.make_timer_label(mf)
        self.timer_lbl.place(relx=0.97, rely=0.05, anchor="ne")

        # START / PAUSE / STOP nupud paremas alumises nurgas
        # Kasutame tavalist tk.Frame, et taust ei oleks hall
        btns = ui_styles.make_bottom_bar(mf)
        # paremas alumises nurgas
        btns.place(relx=0.98, rely=0.98, anchor="se")

        # Nupud ise teeme tk.Button-iga, et värvid täpselt töötaks
        button_font = ("Bernoru SemiCondensed", 18, "bold")

        self.start_btn = tk.Button(
            btns,
            text="START",
            font=button_font,
            fg="black",
            bd=0,
            relief="flat",
            command=self.on_start,
        )
        ui_styles.style_control_button(self.start_btn)

        self.pause_btn = tk.Button(
            btns,
            text="PAUSE",
            font=button_font,
            fg="black",
            bd=0,
            relief="flat",
            command=self.on_pause,
        )
        ui_styles.style_control_button(self.pause_btn)

        self.stop_btn = tk.Button(
            btns,
            text="STOP",
            font=button_font,
            fg="black",
            bd=0,
            relief="flat",
            command=self.on_stop,
        )
        ui_styles.style_control_button(self.stop_btn)

        # Paigutame nupud ühte ritta
        self.start_btn.grid(row=0, column=0, padx=10)
        self.pause_btn.grid(row=0, column=1, padx=10)
        self.stop_btn.grid(row=0, column=2, padx=10)

    # Muusika toggle tuleb SideMenu-st
    def _on_music_toggle(self, value: str) -> None:
        # MusicPlayer API järgi on see handle_toggle()
        self.music.handle_toggle(value)

        # kui keerati ON ja me oleme focusingus, hakkame kohe mängima
        if (value or "").strip().lower() == "on" and self.state == "focusing":
            self.music.start_for_focusing()

    # Nuppude funktsioonid
    def on_start(self) -> None:
        """Käivitab uue fookussessiooni."""
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

        # Muusika ainult focusing ajal
        self.music.start_for_focusing()

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
        """Lülitab taimeri pausile või jätkab (PAUSE/RESUME)."""
        # 1) Aktiivse sessiooni pausile panemine
        if self.state in ("focusing", "break") and self.end_ts:
            left = max(0.0, self.end_ts - time.time())
            self.paused_left = left

            # Pausil muusika pausile
            self.music.pause()

            # jätame meelde, mis faasis pausile läksime
            if self.state == "focusing":
                self.state = "paused_focusing"
            else:
                self.state = "paused_break"

            self.end_ts = None
            self.timer_lbl.configure(text=format_mmss(left))

            self.progress["mood"] = "sad"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

            self.status_lbl.configure(text="Paused.", foreground="#b26a00")

            # nupp PAUSE -> RESUME
            self.pause_btn.configure(text="RESUME")

        # 2) Pausilt jätkamine
        elif self.state in ("paused_focusing", "paused_break") and self.paused_left is not None:
            if self.state == "paused_focusing":
                self.state = "focusing"
                mood = "neutral"
            else:
                self.state = "break"
                mood = "neutral"

            # kui tagasi focusingusse, siis muusika edasi
            if self.state == "focusing":
                self.music.unpause()
                self.music.start_for_focusing()
            else:
                self.music.stop()

            self.end_ts = time.time() + self.paused_left
            self.paused_left = None

            self.progress["mood"] = mood
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

            self.status_lbl.configure(text="Resumed.", foreground="#2e7d32")

            # nupp RESUME -> PAUSE
            self.pause_btn.configure(text="PAUSE")

    def on_stop(self) -> None:
        """Tühistab sessiooni täielikult."""
        if self.state in ("focusing", "break", "paused_focusing", "paused_break"):
            self.state = "idle"
            self.music.stop()
            self.end_ts = None
            self.paused_left = None
            self.current_cycle = 0
            self.timer_lbl.configure(text="00:00")
            self.progress["mood"] = "sad"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()
            self.status_lbl.configure(
                text="Session cancelled - no points added.", foreground="#e53935"
            )
            # nupp tagasi PAUSE peale
            self.pause_btn.configure(text="PAUSE")

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
                    self.progress["last_session"] = datetime.now().isoformat(timespec="seconds")
                    save_progress(self.progress)  # type: ignore[arg-type]
                    self.points_lbl.configure(text=f"Points: {float(self.progress['total']):.1f}")
                    self._grow_stage_if_needed()

                    # Kass on rõõmus
                    self.progress["mood"] = "happy"
                    save_progress(self.progress)  # type: ignore[arg-type]
                    self._render_scene()

                    if self.current_cycle < self.total_cycles:
                        # läheb pausile
                        self.music.stop()
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
                        self.music.stop()
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
                    # paus lõppes, uus fookus
                    self.current_cycle += 1
                    self.state = "focusing"
                    self.end_ts = time.time() + self.focus_len_min * 60

                    # focusing algab -> muusika
                    self.music.start_for_focusing()

                    self.status_lbl.configure(
                        text=f"Session {self.current_cycle}/{self.total_cycles} started!",
                        foreground="#866a24",
                    )
                    self.progress["mood"] = "neutral"
                    save_progress(self.progress)  # type: ignore[arg-type]
                    self._render_scene()

        # tick() tahab is_focusing parameetrit
        self.music.tick(is_focusing=(self.state == "focusing"))

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
    root.state("zoomed")            # aken kohe maksimeeritud
    root.configure(bg="#f5f5f5")  # taust, kui pilt ei kata kõike
    App(root)
    root.mainloop()
