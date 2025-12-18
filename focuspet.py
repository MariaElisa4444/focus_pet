"""
Projekt: Focus Pet – fookustaimer koos kasvava kassiga
Autorid: Maria Elisa Vassiljeva, Viktorija Korjagina
Käivitamisjuhend:
    1. Laadi alla projekti ZIP fail ja paki see lahti
    2. Veendu, et Python 3.10+ on installitud
    3. Ava terminal ja paigalda vajalikud teegid: pip install pillow pygame
    4. Liigu kaustasse, kuhu programm on salvestatud: cd (programmi kausta tee)
    5. Käivita programm: python focuspet.py
"""


from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, ttk

from menu_panel import SideMenu  # meie eraldi failis olev külgmenüü
import ui_styles  # kujundus (värvid, fondid, nupu stiilid) on eraldi failis

# Muusika jaoks kasutame pygame.mixer teeki
# (kui pygame pole installitud, muusika lihtsalt ei tööta, aga programm töötab edasi)
try:
    import pygame  # type: ignore
except Exception:
    pygame = None  # type: ignore

# Eraldi failides
from music_player import MusicPlayer  # muusika loogika
import config as cfg # projekti seaded (tee, valikud, pildid, tasemed)
from progress_store import load_progress, save_progress  # kassi seisu lugemine/salvestamine
from image_utils import format_mmss, load_photo_fit # pildi laadimine ja aja kuvamine
from toast_manager import ToastManager # ajutised sõnumid
from timer import TimerEngine # taimeri olekumasin

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
        self._img_cache = None
        self._splash_img_cache = None

        # Kassi ja progressi olek
        self.progress = load_progress()

        # Taimeri olek
        self.engine = TimerEngine()

        # Muusika
        self.music = MusicPlayer(assets_path=cfg.ASSETS, pygame_module=pygame)

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
        image_path = cfg.IMAGES / cfg.START_SCREEN_FILE
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
        self.music.sfx("button")
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
            assets_path=cfg.ASSETS,
            focus_choices=cfg.FOCUS_CHOICES,
            sessions_choices=cfg.SESSIONS_CHOICES,
            break_choices=cfg.BREAK_CHOICES,
            initial_points=float(self.progress["total"]),
            on_update_scene=self._render_scene,
            on_music_toggle=self._on_music_toggle,
        )

        # Seome comboboxid ja sildid nii, et ülejäänud kood ei muutuks
        self.focus_cb = self.menu.focus_cb
        self.sessions_cb = self.menu.sessions_cb
        self.break_cb = self.menu.break_cb
        self.points_lbl = self.menu.points_label

        # Taimer paremas ülanurgas
        # Kasutame tk.Label, et saaksime taustavärvi panna
        self.timer_lbl = ui_styles.make_timer_label(mf)
        self.timer_lbl.place(relx=0.97, rely=0.05, anchor="ne")

        # HUD (püsiv info: focus/break/pause)
        self.hud_lbl = ui_styles.make_hud_label(mf)
        self._update_hud()
        self.hud_lbl.place(relx=0.97, rely=0.17, anchor="ne")

        # TOAST ajutine teade
        self.toast_frame, self.toast_lbl = ui_styles.make_toast(mf)
        self.toast = ToastManager(self.root, self.toast_frame, self.toast_lbl)

        # START / PAUSE / STOP nupud
        btns = ui_styles.make_bottom_bar(mf)
        btns.place(relx=0.98, rely=0.98, anchor="se")

        self.start_btn, self.pause_btn, self.stop_btn = ui_styles.make_control_buttons(
            btns,
            on_start=self.on_start,
            on_pause=self.on_pause,
            on_stop=self.on_stop,
        )

    # Muusika toggle tuleb SideMenu-st
    def _on_music_toggle(self, value: str) -> None:
        # MusicPlayer API järgi on see handle_toggle()
        self.music.handle_toggle(value)

        # kui keerati ON ja me oleme focusingus, hakkame kohe mängima
        if (value or "").strip().lower() == "on" and self.engine.state == "focusing":
            self.music.start_for_focusing()

    # Nuppude funktsioonid
    def on_start(self) -> None:
        """Käivitab uue fookussessiooni."""
        self.music.sfx("button")

        if self.engine.state not in ("idle", "break"):
            return

        try:
            focus_min = float(self.focus_cb.get())
        except Exception:
            focus_min = 25.0

        try:
            cycles = int(self.sessions_cb.get())
        except Exception:
            cycles = 3

        try:
            break_min = float(self.break_cb.get())
        except Exception:
            break_min = 5.0

        self.engine.start(focus_min, break_min, cycles)

        if self.engine.state == "focusing":
            self.music.start_for_focusing()

        left = self.engine.seconds_left() or 0.0
        self.timer_lbl.configure(text=format_mmss(left))

        if self.progress["mood"] == "sad":
            self.progress["mood"] = "neutral"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

        self._update_hud()
        self.toast.show(f"Session {self.engine.current_cycle}/{self.engine.total_cycles} started!", kind="info")


    def on_pause(self) -> None:
        """Lülitab taimeri pausile või jätkab (PAUSE/RESUME)."""
        self.music.sfx("button")

        before = self.engine.state
        self.engine.pause_toggle()
        after = self.engine.state

        left = self.engine.seconds_left()
        if left is not None:
            self.timer_lbl.configure(text=format_mmss(left))

        if after in ("paused_focusing", "paused_break"):
            self.music.pause()
            self.pause_btn.configure(text="RESUME")

            self.progress["mood"] = "sad"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

            self.toast.show("Paused", kind="info")

        elif before in ("paused_focusing", "paused_break") and after in ("focusing", "break"):
            self.pause_btn.configure(text="PAUSE")

            if after == "focusing":
                self.music.unpause()
                self.music.start_for_focusing()
            else:
                self.music.stop()

            self.progress["mood"] = "neutral"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

            self.toast.show("Resumed", kind="info")

        self._update_hud()


    def on_stop(self) -> None:
        """Tühistab sessiooni täielikult."""
        self.music.sfx("button")

        if self.engine.state in ("focusing", "break", "paused_focusing", "paused_break"):
            self.engine.stop()

            self.music.stop()
            self.timer_lbl.configure(text="00:00")

            self.progress["mood"] = "sad"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

            self.pause_btn.configure(text="PAUSE")
            self._update_hud()
            self.toast.show("Session cancelled", kind="error")


    def _update_hud(self) -> None:
        """Uuendab püsivat HUD teksti (Ready/Session/Break/Paused)."""
        self.hud_lbl.configure(text=self.engine.hud_text())


    # Taimeri tsükkel
    def _tick(self) -> None:
        """Uuendab taimerit ja reageerib oleku muutustele."""
        left = self.engine.seconds_left()
        if left is not None:
            self.timer_lbl.configure(text=format_mmss(left))

        event = self.engine.tick()

        if event == "focus_finished":
            gained = self.engine.focus_len_min * cfg.POINTS_PER_MINUTE
            self.progress["total"] = float(self.progress["total"]) + gained
            self.progress["last_session"] = datetime.now().isoformat(timespec="seconds")
            save_progress(self.progress)  # type: ignore[arg-type]
            self.points_lbl.configure(text=f"Points: {float(self.progress['total']):.1f}")
            self._grow_stage_if_needed()

            old_mood = str(self.progress.get("mood", "sad"))
            self.progress["mood"] = "happy"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

            self.music.sfx("timer")
            if old_mood != "happy":
                self.music.sfx("meow", cooldown=0.25)

            # anname SFX-ile hetke aega kõlada, siis peatame taustamuusika
            self.root.after(300, self.music.stop)
            self.toast.show(
                f"Focus session finished! (+{gained:.1f}) Break {self.engine.break_len_min:g} min",
                kind="info",
            )

        elif event == "break_finished":
            self.music.start_for_focusing()
            self.music.sfx("timer")

            self.progress["mood"] = "neutral"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

            self.toast.show("Break ended. Back to focus!", kind="info")

        elif event == "all_done":
            # Viimase fookussessiooni punktid (kuna engine annab all_done otse)
            gained = self.engine.focus_len_min * cfg.POINTS_PER_MINUTE
            self.progress["total"] = float(self.progress["total"]) + gained
            self.progress["last_session"] = datetime.now().isoformat(timespec="seconds")
            save_progress(self.progress)  # type: ignore[arg-type]
            self.points_lbl.configure(text=f"Points: {float(self.progress['total']):.1f}")
            self._grow_stage_if_needed()

            # Lõpuheli (enne stop'i!)
            old_mood = str(self.progress.get("mood", "sad"))
            self.music.sfx("timer")
            if old_mood != "happy":
                self.music.sfx("meow", cooldown=0.25)

            # Lõpuseis (muusika kinni, tuju happy)
            self.root.after(300, self.music.stop)
            self.timer_lbl.configure(text="00:00")

            self.progress["mood"] = "happy"
            save_progress(self.progress)  # type: ignore[arg-type]
            self._render_scene()

            self.toast.show("Good job! All sessions done :)", kind="info")

        self.music.tick(is_focusing=(self.engine.state == "focusing"))
        self._update_hud()
        self.root.after(200, self._tick)

    # Tase kasvab
    def _grow_stage_if_needed(self) -> None:
        """Kontrollib, kas punktid on piisavad järgmisele tasemele liikumiseks."""
        stage = str(self.progress.get("stage", "baby"))
        total = float(self.progress.get("total", 0.0))

        if stage == "baby" and total >= cfg.GROW_THRESHOLDS["baby"]:
            self.progress["stage"] = "teen"
        elif stage == "teen" and total >= cfg.GROW_THRESHOLDS["teen"]:
            self.progress["stage"] = "adult"

        save_progress(self.progress)  # type: ignore[arg-type]

    # Pildi joonistamine
    def _current_image_path(self) -> Path:
        """Tagastab pildi tee (tase + tuju) järgi."""
        stage = str(self.progress.get("stage", "baby"))
        mood = str(self.progress.get("mood", "sad"))
        return cfg.IMAGES / cfg.SCENES[stage][mood]

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
