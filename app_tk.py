import json, time
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# Пути
ROOT = Path(__file__).parent
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"
SPRITES = ASSETS / "sprites"
UI = ASSETS / "ui"
PROGRESS = DATA / "progress.json"

# Параметры
FOCUS_CHOICES = [0.1, 1, 5, 10, 15, 20, 25, 30, 40, 45, 50, 60]
SESSIONS_CHOICES = list(range(1, 9))
BREAK_CHOICES = [0.1, 1, 2, 3, 5, 7, 10, 15, 20, 25]
POINTS_PER_MIN = 1

LEVELS = [
    {"min_total": 0.0, "name": "baby",  "file": "baby.png",  "label": "Baby"},
    {"min_total": 0.3, "name": "teen",  "file": "teen.png",  "label": "Teen"},
    {"min_total": 0.5, "name": "adult", "file": "adult.png", "label": "Adult"},
]
SAD_FILE = "sad.png"
BG_FILE = (UI / "bg.png") if (UI / "bg.png").exists() else None

# Размер «холста» под картинку
CANVAS_W, CANVAS_H = 720, 440

# ---------- Утилиты ----------
def load_progress():
    defaults = {"total": 0.0, "level": "baby", "last_session": None, "mood": "normal"}
    try:
        if PROGRESS.exists():
            raw = PROGRESS.read_text(encoding="utf-8").strip()
            data = json.loads(raw) if raw else {}
        else:
            data = {}
    except Exception:
        data = {}

    # миграция/приведение типов
    total = data.get("total", 0)
    try:
        total = float(total)
    except Exception:
        total = 0.0

    level = data.get("level", "baby")
    if level not in {"baby", "teen", "adult"}:
        level = "baby"

    mood = data.get("mood", "normal")
    if mood not in {"normal", "sad"}:
        mood = "normal"

    prog = {
        "total": total,
        "level": level,
        "last_session": data.get("last_session", None),
        "mood": mood
    }
    save_progress(prog)
    return prog

def save_progress(p):
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

def level_by_total(total: float):
    lvl = LEVELS[0]
    for x in LEVELS:
        if total >= float(x["min_total"]):
            lvl = x
    return lvl

def format_mmss(sec: float):
    s = max(0, int(round(sec)))
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"

# Картинки
def load_image(path: Path, max_w: int, max_h: int) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    scale = min(max_w / w, max_h / h, 1.0)
    if scale != 1.0:
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    return img

def compose_cat_on_bg(sprite_file: str) -> Image.Image:
    cat_path = SPRITES / sprite_file
    if not cat_path.exists():
        return Image.new("RGBA", (CANVAS_W, CANVAS_H), (240,240,240,255))

    cat = load_image(cat_path, CANVAS_W, CANVAS_H)
    if BG_FILE:
        bg = load_image(BG_FILE, CANVAS_W, CANVAS_H)
        # уменьшаем кота до ~60% поля, центрируем
        target_w, target_h = int(CANVAS_W*0.6), int(CANVAS_H*0.6)
        cat = cat.resize((min(cat.width, target_w), min(cat.height, target_h)), Image.LANCZOS)
        x = (bg.width - cat.width)//2
        y = (bg.height - cat.height)//2
        comp = bg.copy()
        comp.alpha_composite(cat, (x, y))
        return comp
    else:
        base = Image.new("RGBA", (CANVAS_W, CANVAS_H), (240,240,240,255))
        x = (CANVAS_W - cat.width)//2
        y = (CANVAS_H - cat.height)//2
        base.alpha_composite(cat, (x, y))
        return base

# ---------- Приложение ----------
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("🐾 Focus Pet — Cycles (tkinter)")
        root.resizable(False, False)

        # состояние
        self.progress = load_progress()
        self.state = "idle"      # idle|focusing|break
        self.end_ts = None
        self.focus_len = 25.0
        self.break_len = 5.0
        self.total_cycles = 1
        self.current_cycle = 0
        self.sad_until = 0.0     # timestamp до которого показываем sad

        # UI
        main = ttk.Frame(root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")

        # Левый блок — изображение питомца
        self.canvas = tk.Canvas(main, width=CANVAS_W, height=CANVAS_H, bg="#f3f3f3", highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=8, padx=(0, 16))

        # Правый блок — параметры
        ttk.Label(main, text="⏱️ Длительность фокуса (мин)").grid(row=0, column=1, sticky="w")
        self.focus_cb = ttk.Combobox(main, state="readonly", width=8,
                                     values=[str(x) for x in FOCUS_CHOICES])
        self.focus_cb.set("25")
        self.focus_cb.grid(row=1, column=1, sticky="w", pady=(0,8))

        ttk.Label(main, text="🔁 Кол-во сессий").grid(row=2, column=1, sticky="w")
        self.sessions_cb = ttk.Combobox(main, state="readonly", width=8,
                                        values=[str(x) for x in SESSIONS_CHOICES])
        self.sessions_cb.set("1")
        self.sessions_cb.grid(row=3, column=1, sticky="w", pady=(0,8))

        ttk.Label(main, text="🍵 Перерыв (мин)").grid(row=4, column=1, sticky="w")
        self.break_cb = ttk.Combobox(main, state="readonly", width=8,
                                     values=[str(x) for x in BREAK_CHOICES])
        self.break_cb.set("5")
        self.break_cb.grid(row=5, column=1, sticky="w", pady=(0,8))

        # Кнопки
        btns = ttk.Frame(main)
        btns.grid(row=6, column=1, sticky="w", pady=(6,6))
        self.start_btn = ttk.Button(btns, text="▶️ Start", command=self.on_start)
        self.finish_btn = ttk.Button(btns, text="⏹️ Finish", command=self.on_finish)
        self.start_btn.grid(row=0, column=0, padx=(0,8))
        self.finish_btn.grid(row=0, column=1)

        # Таймер/статус
        self.cycle_lbl = ttk.Label(main, text="Цикл: 0/1")
        self.cycle_lbl.grid(row=7, column=1, sticky="w", pady=(6,0))

        self.timer_lbl = ttk.Label(main, text="00:00", font=("Consolas", 36))
        self.timer_lbl.grid(row=8, column=0, columnspan=2, sticky="we", pady=(8,4))

        self.status_lbl = ttk.Label(main, text="", foreground="#2e7d32")
        self.status_lbl.grid(row=9, column=0, columnspan=2, sticky="w")

        # Инфо по очкам/уровню
        info = ttk.Frame(main)
        info.grid(row=10, column=0, columnspan=2, sticky="we", pady=(6,0))
        ttk.Label(info, text="Очков:").grid(row=0, column=0, sticky="w")
        self.points_val = ttk.Label(info, text=str(self.progress["total"]), font=("Segoe UI", 10, "bold"))
        self.points_val.grid(row=0, column=1, sticky="w", padx=(4,12))
        ttk.Label(info, text="Уровень:").grid(row=0, column=2, sticky="w")
        self.level_val = ttk.Label(info, text=self.progress["level"], font=("Segoe UI", 10, "bold"))
        self.level_val.grid(row=0, column=3, sticky="w", padx=(4,0))

        # первая отрисовка кота
        self._img_cache = None
        self.update_cat_image()

        # «тик»
        self.root.after(200, self.tick)

    # ---- модель ----
    def set_message(self, msg, color="#2e7d32"):
        self.status_lbl.configure(text=msg, foreground=color)

    def update_cat_image(self):
        if self.progress.get("mood", "normal") == "sad":
            sprite = SAD_FILE
            caption = f"Кот грустит 😿 • Очков: {self.progress['total']:.1f}"
        else:
            lvl = level_by_total(self.progress["total"])
            sprite = lvl["file"]
            caption = f"{lvl['label']} • Очков: {self.progress['total']:.1f}"
        img = compose_cat_on_bg(sprite).convert("RGB")
        self._img_cache = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(CANVAS_W//2, CANVAS_H//2, image=self._img_cache)
        self.canvas.create_text(CANVAS_W//2, 20, text=caption, fill="#222", font=("Segoe UI", 11, "bold"))

    def disable_controls(self, disabled: bool):
        state = "disabled" if disabled else "readonly"
        self.focus_cb.configure(state=state)
        self.sessions_cb.configure(state=state)
        self.break_cb.configure(state=state)
        self.start_btn.configure(state=("disabled" if disabled else "normal"))
        self.finish_btn.configure(state=("normal" if disabled else "disabled"))

    # ---- кнопки ----
    def on_start(self):
        if self.state != "idle":
            return
        try:
            self.focus_len = float(self.focus_cb.get())
        except Exception:
            self.focus_len = 25.0
        try:
            self.total_cycles = int(self.sessions_cb.get())
        except Exception:
            self.total_cycles = 1
        try:
            self.break_len = float(self.break_cb.get())
        except Exception:
            self.break_len = 5.0

        # старт цикла
        self.current_cycle = 1
        self.state = "focusing"
        self.end_ts = time.time() + self.focus_len * 60.0
        self.set_message(f"Сессия 1 из {self.total_cycles} началась. Удачи! 💪")
        self.cycle_lbl.configure(text=f"Цикл: {self.current_cycle}/{self.total_cycles}")
        self.disable_controls(True)

    def on_finish(self):
        # досрочно — всё прерываем, грустим
        if self.state in ("focusing", "break"):
            self.state = "idle"
            self.end_ts = None
            self.current_cycle = 0
            self.progress["mood"] = "sad"
            save_progress(self.progress)
            self.set_message("Сессия прервана — очки не начислены. Кот грустит 😿", color="#e53935")
            self.timer_lbl.configure(text="00:00")
            # показать sad на 3 сек
            self.update_cat_image()
            self.sad_until = time.time() + 3.0
            self.disable_controls(False)

    # ---- тик ----
    def tick(self):
        now = time.time()

        # вернуть кота после sad
        if self.sad_until and now >= self.sad_until:
            self.sad_until = 0.0
            self.update_cat_image()

        # таймер
        if self.state in ("focusing", "break") and self.end_ts:
            remaining = self.end_ts - now
            self.timer_lbl.configure(text=format_mmss(remaining))

            if remaining <= 0:
                if self.state == "focusing":
                    # Успешно завершили фокус — начисляем очки, снимаем грусть
                    gained = self.focus_len * POINTS_PER_MIN
                    self.progress["total"] = float(self.progress["total"]) + float(gained)
                    new_lvl = level_by_total(self.progress["total"])
                    self.progress["level"] = new_lvl["name"]
                    self.progress["last_session"] = datetime.now().isoformat(timespec="seconds")
                    self.progress["mood"] = "normal"
                    save_progress(self.progress)

                    self.points_val.configure(text=f"{self.progress['total']:.1f}")
                    self.level_val.configure(text=self.progress["level"])
                    self.update_cat_image()

                    if self.current_cycle < self.total_cycles:
                        # идём на перерыв
                        self.state = "break"
                        self.end_ts = time.time() + self.break_len * 60.0
                        self.set_message(
                            f"🎉 Сессия {self.current_cycle} завершена (+{gained:.1f} очков). "
                            f"Перерыв {self.break_len:g} мин 🍵"
                        )
                    else:
                        # всё завершено
                        self.state = "idle"
                        self.end_ts = None
                        self.current_cycle = 0
                        self.set_message(
                            f"🎉 Все {self.total_cycles} сессий завершены. "
                            f"+{gained:.1f} очков за последнюю."
                        )
                        self.timer_lbl.configure(text="00:00")
                        self.disable_controls(False)

                elif self.state == "break":
                    # перерыв закончился -> следующая фокус-сессия
                    self.current_cycle += 1
                    self.state = "focusing"
                    self.end_ts = time.time() + self.focus_len * 60.0
                    self.set_message(f"Сессия {self.current_cycle} из {self.total_cycles} началась. Поехали! 💪")
                    self.cycle_lbl.configure(text=f"Цикл: {self.current_cycle}/{self.total_cycles}")

        # планируем следующий тик
        self.root.after(200, self.tick)

# ---------- Запуск ----------
if __name__ == "__main__":
    root = tk.Tk()
    # Немного приятной темы (если есть)
    try:
        style = ttk.Style()
        for theme in ("vista", "xpnative", "clam"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break
    except Exception:
        pass

    app = App(root)
    root.mainloop()