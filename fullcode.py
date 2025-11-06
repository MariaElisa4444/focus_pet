# focus_pet_app.py
# Python stdlib + Pillow
import json, time
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# ---------- Пути ----------
ROOT = Path(__file__).parent
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"
PROGRESS = DATA / "progress.json"

# Параметры таймера
FOCUS_CHOICES   = [0.1, 1, 5, 10, 15, 20, 25, 30, 40, 45, 50, 60]
SESSIONS_CHOICES= list(range(1, 9))   # пользователь может менять; по ТЗ «полная» обычно = 3
BREAK_CHOICES   = [0.1, 1, 2, 3, 5, 7, 10, 15, 20, 25]
POINTS_PER_MIN  = 1

# Настройки сцен (фон+кот уже объединены — используем готовые изображения)
START_SCREEN_BG = "focuspet1.png"

# Стадии/настроения
STAGES = ("baby", "teen", "adult")
MOODS  = ("sad", "neutral", "happy")

# Карты файлов сцен по стадии и настроению
SCENES = {
    "baby":  {"sad": "baby_sad.png",  "neutral": "baby_neutral.png",  "happy": "baby_happy.png"},
    "teen":  {"sad": "teen_sad.png",  "neutral": "teen_neutral.png",  "happy": "teen_happy.png"},
    "adult": {"sad": "adult_sad.png", "neutral": "adult_neutral.png", "happy": "adult_happy.png"},
}
ADULT_REST_FRAMES = ["adult_rest1.png", "adult_rest2.png", "adult_rest3.png"]  # перерыв-анимация

# «Долгое отсутствие» — после этого кот станет sad
IDLE_SECONDS = 60 * 60   # 1 час

# Размер сцены (логический); фактически будем подгонять под окно
SCENE_W, SCENE_H = 1280, 720

# ---------- Утилиты ----------
def format_mmss(sec: float) -> str:
    s = max(0, int(round(sec)))
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"

def load_photo_fit(path: Path, max_w: int, max_h: int) -> ImageTk.PhotoImage:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    scale = min(max_w / w, max_h / h, 1.0)
    if scale != 1.0:
        img = img.resize((max(1, int(w*scale)), max(1, int(h*scale))), Image.LANCZOS)
    return ImageTk.PhotoImage(img)

# ---------- Прогресс (сохраняем очки, и дополнительно stage/mood/last_login) ----------
def load_progress():
    defaults = {"total": 0.0, "stage": "baby", "mood": "sad", "last_session": None, "last_login": time.time()}
    try:
        if PROGRESS.exists():
            raw = PROGRESS.read_text(encoding="utf-8").strip()
            data = json.loads(raw) if raw else {}
        else:
            data = {}
    except Exception:
        data = {}
    # нормализация
    total = data.get("total", 0.0)
    try:
        total = float(total)
    except Exception:
        total = 0.0
    stage = data.get("stage", "baby");  stage = stage if stage in STAGES else "baby"
    mood  = data.get("mood", "sad");    mood  = mood  if mood  in MOODS  else "sad"
    last_session = data.get("last_session", None)
    last_login   = float(data.get("last_login", time.time()))
    prog = {"total": total, "stage": stage, "mood": mood, "last_session": last_session, "last_login": last_login}
    save_progress(prog)
    return prog

def save_progress(p):
    p = dict(p)
    p["last_login"] = time.time()
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Приложение ----------
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("🐾 Focus Pet — Tkinter")
        root.geometry("1280x800")
        root.minsize(960, 640)

        # ===== Состояния (таймер и очки — как в вашем appp_tk.py) =====
        self.progress = load_progress()  # total/stage/mood/last_session
        self.state = "idle"              # idle|focusing|break
        self.end_ts = None
        self.focus_len = 25.0
        self.break_len = 5.0
        self.total_cycles = 3            # по умолчанию полная сессия = 3
        self.current_cycle = 0
        self.sad_until = 0.0             # секунд до автоснятия sad-перекрытия

        # Для idle-слежения
        self.last_active_ts = time.time()

        # Анимация перерыва у adult
        self.rest_idx = 0
        self._rest_last_ms = 0
        self.REST_FPS_MS = 350

        # ===== UI: два экрана =====
        self.container = ttk.Frame(root)
        self.container.pack(fill="both", expand=True)
        self.container.bind("<Configure>", self._on_resize)

        # --- Стартовый экран ---
        self.start_frame = ttk.Frame(self.container)
        self.start_bg_label = ttk.Label(self.start_frame)  # фон-картинка
        self.start_bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.title_lbl = ttk.Label(self.start_frame, text="Focus Pet",
                                   foreground="#FFFFFF",
                                   font=("Arial Rounded MT Bold", 64))
        self.start_btn = ttk.Button(self.start_frame, text="START", command=self.enter_main)
        # Размещаем по центру
        self.title_lbl.place(relx=0.5, rely=0.38, anchor="center")
        self.start_btn.place(relx=0.5, rely=0.60, anchor="center", width=240, height=64)

        # --- Основной экран ---
        self.main_frame = ttk.Frame(self.container)

        # Сцена (фон+кот — готовая картинка)
        self.scene_label = ttk.Label(self.main_frame)
        self.scene_label.place(relx=0.5, rely=0.5, anchor="center")

        # Таймер (правый верхний угол)
        self.timer_lbl = ttk.Label(self.main_frame, text="00:00", foreground="#222222", font=("Consolas", 28, "bold"))
        self.timer_lbl.place(relx=0.98, rely=0.04, anchor="ne")

        # Кнопки (правый нижний угол)
        self.btn_start = ttk.Button(self.main_frame, text="▶ START", command=self.on_start)
        self.btn_pause = ttk.Button(self.main_frame, text="⏸ PAUSE", command=self.on_pause)
        self.btn_stop  = ttk.Button(self.main_frame, text="⏹ STOP",  command=self.on_stop)
        self.btn_start.place(relx=0.70, rely=0.95, anchor="s", width=120, height=44)
        self.btn_pause.place(relx=0.84, rely=0.95, anchor="s", width=120, height=44)
        self.btn_stop.place( relx=0.97, rely=0.95, anchor="s", width=120, height=44)

        # Селекторы времени (слева сверху)
        self.side_panel = ttk.Frame(self.main_frame)
        self.side_panel.place(relx=0.02, rely=0.04, anchor="nw")

        ttk.Label(self.side_panel, text="⏱ Фокус (мин)").grid(row=0, column=0, sticky="w")
        self.focus_cb = ttk.Combobox(self.side_panel, state="readonly", width=8, values=[str(x) for x in FOCUS_CHOICES])
        self.focus_cb.set("25")
        self.focus_cb.grid(row=1, column=0, sticky="w", pady=(0,6))

        ttk.Label(self.side_panel, text="🔁 Сессий").grid(row=2, column=0, sticky="w")
        self.sessions_cb = ttk.Combobox(self.side_panel, state="readonly", width=8, values=[str(x) for x in SESSIONS_CHOICES])
        self.sessions_cb.set("3")
        self.sessions_cb.grid(row=3, column=0, sticky="w", pady=(0,6))

        ttk.Label(self.side_panel, text="🍵 Перерыв (мин)").grid(row=4, column=0, sticky="w")
        self.break_cb = ttk.Combobox(self.side_panel, state="readonly", width=8, values=[str(x) for x in BREAK_CHOICES])
        self.break_cb.set("5")
        self.break_cb.grid(row=5, column=0, sticky="w")

        # Очки/состояние
        self.points_label = ttk.Label(self.main_frame, text=f"Очки: {self.progress['total']:.1f}",
                                      font=("Segoe UI", 10, "bold"))
        self.points_label.place(relx=0.02, rely=0.10, anchor="nw")
        self.status_lbl = ttk.Label(self.main_frame, text="", foreground="#2e7d32")
        self.status_lbl.place(relx=0.02, rely=0.14, anchor="nw")

        # Отрисовка стартового экрана
        self._start_bg_cache = None
        self._scene_cache = None
        self.show_start()

        # Глобальное слежение за активностью для idle→sad
        for seq in ("<Key>", "<Button-1>", "<Motion>"):
            self.root.bind_all(seq, self._mark_active, add="+")

        # главный тик
        self.root.after(200, self._tick)

        # Небольшая тема, как у вас
        try:
            style = ttk.Style()
            for theme in ("vista", "xpnative", "clam"):
                if theme in style.theme_names():
                    style.theme_use(theme)
                    break
        except Exception:
            pass

    # ---------- Экран: старт ----------
    def show_start(self):
        self.main_frame.place_forget()
        self.start_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._update_start_bg()
        # до начала — грустный
        self.progress["mood"] = "sad"
        save_progress(self.progress)

    def enter_main(self):
        self.start_frame.place_forget()
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._render_scene()  # показать кота с текущей стадией/настроением
        self.timer_lbl.configure(text="00:00")
        self.state = "idle"
        self._set_status("Нажмите START, чтобы начать первую сессию")

    # ---------- Таймер/кнопки (логика из вашего appp_tk.py) ----------
    def on_start(self):
        if self.state not in ("idle", "break"):  # запрещаем повторный старт в середине фокуса
            return
        try:
            self.focus_len = float(self.focus_cb.get())
        except Exception:
            self.focus_len = 25.0
        try:
            self.total_cycles = int(self.sessions_cb.get())
        except Exception:
            self.total_cycles = 3
        try:
            self.break_len = float(self.break_cb.get())
        except Exception:
            self.break_len = 5.0

        if self.state == "idle":
            self.current_cycle = 1
        # старт/рестарт учебного блока (из break или idle)
        self.state = "focusing"
        self.end_ts = time.time() + self.focus_len * 60.0
        self._set_status(f"Сессия {self.current_cycle} из {self.total_cycles} началась. Удачи! 💪")
        self.timer_lbl.configure(text=format_mmss(self.end_ts - time.time()))
        # при старте — выводим neutral, если был sad
        if self.progress.get("mood") == "sad":
            self.progress["mood"] = "neutral"
            save_progress(self.progress)
            self._render_scene()

    def on_pause(self):
        # Пауза: останавливаем отсчёт и показываем грусть
        if self.state in ("focusing", "break") and self.end_ts:
            remaining = max(0.0, self.end_ts - time.time())
            # Фиксируем «заморозку»: переключимся в idle, сохраним оставшееся в self.end_ts как None
            self.state = "idle"
            self.end_ts = None
            self.timer_lbl.configure(text=format_mmss(remaining))
            self.progress["mood"] = "sad"
            save_progress(self.progress)
            self._render_scene()
            self._set_status("Пауза. Нажмите START, чтобы продолжить (оставшееся время сохранено визуально).", color="#b26a00")

    def on_stop(self):
        # Полная остановка (как ваш Finish): очки не начисляются, грустим
        if self.state in ("focusing", "break"):
            self.state = "idle"
            self.end_ts = None
            self.current_cycle = 0
            self.progress["mood"] = "sad"
            save_progress(self.progress)
            self._set_status("Сессия прервана — очки не начислены. Кот грустит 😿", color="#e53935")
            self.timer_lbl.configure(text="00:00")
            self._render_scene()

    # ---------- Главный тик (как у вас: remaining → события) ----------
    def _tick(self):
        now = time.time()

        # idle → sad, если давно не трогали
        if now - self.last_active_ts > IDLE_SECONDS and self.progress.get("mood") != "sad":
            self.progress["mood"] = "sad"
            save_progress(self.progress)
            self._render_scene()

        # таймер
        if self.state in ("focusing", "break") and self.end_ts:
            remaining = self.end_ts - now
            self.timer_lbl.configure(text=format_mmss(remaining))

            if remaining <= 0:
                if self.state == "focusing":
                    # ==== УСПЕШНО завершили фокус — НАЧИСЛЯЕМ очки (ваша логика) ====
                    gained = self.focus_len * POINTS_PER_MIN
                    self.progress["total"] = float(self.progress["total"]) + float(gained)
                    self.progress["last_session"] = datetime.now().isoformat(timespec="seconds")
                    # настроение по вашим правилам: после первого учебного блока — neutral
                    if self.current_cycle == 1:
                        self.progress["mood"] = "neutral"
                    save_progress(self.progress)
                    self.points_label.configure(text=f"Очки: {self.progress['total']:.1f}")

                    # смена сцены по ТЗ: «конец учебного времени → радость»
                    self.progress["mood"] = "happy"
                    save_progress(self.progress)
                    self._render_scene()

                    if self.current_cycle < self.total_cycles:
                        # идём на перерыв
                        self.state = "break"
                        self.end_ts = time.time() + self.break_len * 60.0
                        self._set_status(
                            f"🎉 Сессия {self.current_cycle} завершена (+{gained:.1f} очков). Перерыв {self.break_len:g} мин 🍵"
                        )
                    else:
                        # ==== ПОЛНАЯ СЕССИЯ завершена ====
                        self.state = "idle"
                        self.end_ts = None
                        self._set_status(
                            f"🎉 Все {self.total_cycles} сессий завершены. +{gained:.1f} очков за последнюю."
                        )
                        self.timer_lbl.configure(text="00:00")
                        # Рост: baby→teen→adult, если ещё не adult
                        self._grow_stage_if_needed()
                        # Полная сессия = happy
                        self.progress["mood"] = "happy"
                        save_progress(self.progress)
                        self._render_scene()
                        # готово; ждём нового нажатия START
                elif self.state == "break":
                    # перерыв закончился → след. учебная
                    self.current_cycle += 1
                    self.state = "focusing"
                    self.end_ts = time.time() + self.focus_len * 60.0
                    self._set_status(f"Сессия {self.current_cycle} из {self.total_cycles} началась. Поехали! 💪")
                    # на перерыве у adult крутилась анимация — при входе в учебу вернём neutral
                    if self.progress["mood"] == "happy":
                        # можно оставить happy от предыдущего завершения; но на учебе логичнее neutral
                        self.progress["mood"] = "neutral"
                        save_progress(self.progress)
                        self._render_scene()

        # Анимация отдыха у adult во время перерыва
        if self.state == "break" and self._is_adult():
            self._animate_adult_rest()

        self.root.after(200, self._tick)

    # ---------- Стадии/настроения ----------
    def _is_adult(self) -> bool:
        return self.progress.get("stage") == "adult"

    def _grow_stage_if_needed(self):
        stage = self.progress.get("stage", "baby")
        if stage == "baby":
            self.progress["stage"] = "teen"
        elif stage == "teen":
            self.progress["stage"] = "adult"
        # adult остаётся adult
        save_progress(self.progress)

    # ---------- Рендер сцены ----------
    def _current_scene_path(self) -> Path:
        stage = self.progress.get("stage", "baby")
        mood  = self.progress.get("mood", "sad")
        if self.state == "break" and stage == "adult":
            # Кадры отдыха взрослого на перерыве
            fname = ADULT_REST_FRAMES[self.rest_idx % len(ADULT_REST_FRAMES)]
            return ASSETS / fname
        # Обычные сцены по стадии/настроению
        fname = SCENES[stage][mood]
        return ASSETS / fname

    def _render_scene(self):
        p = self._current_scene_path()
        w = self.container.winfo_width()  or SCENE_W
        h = self.container.winfo_height() or SCENE_H
        if not p.exists():
            self.scene_label.configure(text=f"Missing: {p.name}")
            return
        self._scene_cache = load_photo_fit(p, w, h)
        self.scene_label.configure(image=self._scene_cache)

    def _update_start_bg(self):
        p = ASSETS / START_SCREEN_BG
        w = self.container.winfo_width()  or SCENE_W
        h = self.container.winfo_height() or SCENE_H
        if p.exists():
            self._start_bg_cache = load_photo_fit(p, w, h)
            self.start_bg_label.configure(image=self._start_bg_cache)
        else:
            self.start_bg_label.configure(text="")

    # ---------- Вспомогательное ----------
    def _set_status(self, msg, color="#2e7d32"):
        self.status_lbl.configure(text=msg, foreground=color)

    def _mark_active(self, _evt=None):
        self.last_active_ts = time.time()

    def _on_resize(self, _evt):
        # ресайз фона стартового экрана или основной сцены
        if self.start_frame.winfo_ismapped():
            self._update_start_bg()
        else:
            self._render_scene()

# ---------- Запуск ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()