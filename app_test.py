# app_tk.py (fixed: pass width/height in constructors, not in .place)
import json, time
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

# ---------- Paths / constants ----------
ROOT = Path(__file__).parent
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"
SPRITES = ASSETS / "sprites"
UI = ASSETS / "ui"
IMAGES = ROOT / "images"
PROGRESS = DATA / "progress.json"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

CANVAS_W, CANVAS_H = 1100, 700
BTN_KW = dict(height=44, corner_radius=14, fg_color="#1e88e5",
              hover_color="#1565c0", text_color="white", font=("Inter", 16, "bold"))

BG_CANDIDATES = [IMAGES/"focuspet1.png", UI/"bg.png"]
BG_FILE = next((p for p in BG_CANDIDATES if p.exists()), None)

CAT_IMAGES = {
    "neutral": [IMAGES/"cat1.png"],
    "study": [IMAGES/"cat2.png", IMAGES/"cat3.png", IMAGES/"cat4.png"],
    "sleep": [IMAGES/"cat5.png", IMAGES/"cat6.png", IMAGES/"cat7.png"],
    "happy": [IMAGES/"cat8.png", IMAGES/"cat9.png", IMAGES/"cat10.png"],
    "to_sleep": [IMAGES/"cat11.png", IMAGES/"cat12.png"],
    "to_happy": [IMAGES/"cat13.png", IMAGES/"cat14.png"],
    "to_neutral": [IMAGES/"cat15.png", IMAGES/"cat16.png"],
    "study_intermediate": [IMAGES/"cat17.png"],
    "happy_intermediate": [IMAGES/"cat18.png"],
    "sleep_intermediate": [IMAGES/"cat19.png"],
}
LEVELS = [
    {"min_total": 0.0, "name": "baby",  "file": "baby.png",  "label": "Baby"},
    {"min_total": 0.3, "name": "teen",  "file": "teen.png",  "label": "Teen"},
    {"min_total": 0.5, "name": "adult", "file": "adult.png", "label": "Adult"},
]
SAD_FILE = "sad.png"

FOCUS_CHOICES = [0.1, 1, 5, 10, 15, 20, 25, 30, 40, 45, 50, 60]
SESSIONS_CHOICES = list(range(1, 9))
BREAK_CHOICES = [0.1, 1, 2, 3, 5, 7, 10, 15, 20, 25]
POINTS_PER_MIN = 1

def load_progress():
    defaults = {"total": 0.0, "level": "baby", "last_session": None, "mood": "normal"}
    if PROGRESS.exists():
        try:
            data = json.loads(PROGRESS.read_text(encoding="utf-8"))
        except Exception:
            data = defaults
    else:
        data = defaults
    total = float(data.get("total", 0.0))
    level = data.get("level", "baby") if data.get("level") in {"baby","teen","adult"} else "baby"
    mood = data.get("mood", "normal") if data.get("mood") in {"normal","sad"} else "normal"
    out = {"total": total, "level": level, "last_session": data.get("last_session"), "mood": mood}
    PROGRESS.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

def save_progress(p):
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

def level_by_total(total: float):
    lvl = LEVELS[0]
    for x in LEVELS:
        if total >= float(x["min_total"]): lvl = x
    return lvl

def format_mmss(sec: float):
    s = max(0, int(round(sec)))
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"

def open_rgba(path: Path):
    return Image.open(path).convert("RGBA")

def seq_exists(name: str) -> bool:
    return any(Path(p).exists() for p in CAT_IMAGES.get(name, []))

def compose_on_bg(fg_img):
    if BG_FILE and BG_FILE.exists():
        bg = open_rgba(BG_FILE).resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        w, h = fg_img.size
        target_w, target_h = int(CANVAS_W*0.6), int(CANVAS_H*0.6)
        if w > target_w or h > target_h:
            fg_img = fg_img.resize((min(w, target_w), min(h, target_h)), Image.LANCZOS)
        x = (bg.width - fg_img.width)//2
        y = (bg.height - fg_img.height)//2
        bg.alpha_composite(fg_img, (x, y))
        return bg
    base = Image.new("RGBA", (CANVAS_W, CANVAS_H), (245,245,245,255))
    x = (CANVAS_W - fg_img.width)//2
    y = (CANVAS_H - fg_img.height)//2
    base.alpha_composite(fg_img, (x, y))
    return base

def load_level_sprite(sprite_file: str):
    p = SPRITES / sprite_file
    return open_rgba(p) if p.exists() else Image.new("RGBA", (600, 450), (0,0,0,0))

class App:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🐾 Focus Pet — Styled")
        self.root.geometry(f"{CANVAS_W+360}x{CANVAS_H+40}")

        self.progress = load_progress()
        self.state = "idle"
        self.end_ts = None
        self.focus_len = 25.0
        self.break_len = 5.0
        self.total_cycles = 1
        self.current_cycle = 0

        # --- FIXED: width/height passed to constructors ---
        self.image_lbl = ctk.CTkLabel(self.root, text="", width=CANVAS_W, height=CANVAS_H)
        self.image_lbl.place(x=10, y=10)  # no width/height here

        self.panel = ctk.CTkFrame(self.root, corner_radius=16, width=320, height=CANVAS_H)
        self.panel.place(x=CANVAS_W+20, y=10)  # no width/height here

        title = ctk.CTkLabel(self.panel, text="Focus Pet", font=("Inter", 26, "bold"))
        title.pack(pady=(10, 6))

        ctk.CTkLabel(self.panel, text="⏱️ Фокус (мин)").pack(anchor="w", padx=12)
        self.focus_cb = ctk.CTkComboBox(self.panel, values=[str(x) for x in FOCUS_CHOICES], width=120)
        self.focus_cb.set("25")
        self.focus_cb.pack(padx=12, pady=(0,12), anchor="w")

        ctk.CTkLabel(self.panel, text="🔁 Кол-во сессий").pack(anchor="w", padx=12)
        self.sessions_cb = ctk.CTkComboBox(self.panel, values=[str(x) for x in SESSIONS_CHOICES], width=120)
        self.sessions_cb.set("1")
        self.sessions_cb.pack(padx=12, pady=(0,12), anchor="w")

        ctk.CTkLabel(self.panel, text="🍵 Перерыв (мин)").pack(anchor="w", padx=12)
        self.break_cb = ctk.CTkComboBox(self.panel, values=[str(x) for x in BREAK_CHOICES], width=120)
        self.break_cb.set("5")
        self.break_cb.pack(padx=12, pady=(0,12), anchor="w")

        btn_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        btn_row.pack(pady=10, fill="x")
        self.start_btn = ctk.CTkButton(btn_row, text="▶️ Start", command=self.on_start, **BTN_KW)
        self.finish_btn = ctk.CTkButton(btn_row, text="⏹️ Finish", command=self.on_finish, **BTN_KW)
        self.start_btn.pack(side="left", padx=(12,8))
        self.finish_btn.pack(side="left")

        self.cycle_lbl = ctk.CTkLabel(self.panel, text="Цикл: 0/1")
        self.cycle_lbl.pack(padx=12, pady=(8,2), anchor="w")

        self.timer_lbl = ctk.CTkLabel(self.panel, text="00:00", font=("Consolas", 38, "bold"))
        self.timer_lbl.pack(pady=(6,6))

        self.status_lbl = ctk.CTkLabel(self.panel, text="", justify="left")  # wraplength not supported in CTkLabel
        self.status_lbl.pack(padx=12, pady=(0,6), anchor="w")

        info = ctk.CTkFrame(self.panel, fg_color="transparent")
        info.pack(padx=12, pady=(4,0), fill="x")
        ctk.CTkLabel(info, text="Очков:").pack(side="left")
        self.points_val = ctk.CTkLabel(info, text=f"{self.progress['total']:.1f}")
        self.points_val.pack(side="left", padx=(4,12))
        ctk.CTkLabel(info, text="Уровень:").pack(side="left")
        self.level_val = ctk.CTkLabel(info, text=self.progress["level"])
        self.level_val.pack(side="left", padx=(4,0))

        self._imgtk_cache = None
        self.update_cat_image()
        self.root.after(200, self.tick)

    def set_message(self, msg, color="#2e7d32"):
        self.status_lbl.configure(text=msg, text_color=color)

    def _draw_caption(self, img, caption):
        from PIL import ImageDraw, ImageFont
        dr = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arial.ttf", 22)
        except Exception: font = ImageFont.load_default()
        bbox = dr.textbbox((0, 0), caption, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (img.width - tw)//2; y = 12
        dr.text((x+1,y+1), caption, fill=(0,0,0), font=font)
        dr.text((x,y), caption, fill=(255,255,255), font=font)

    def update_cat_image(self):
        if seq_exists("neutral"):
            p = next((p for p in CAT_IMAGES["neutral"] if p.exists()), None)
            img = open_rgba(p) if p else load_level_sprite(level_by_total(self.progress["total"])["file"])
        else:
            img = load_level_sprite(level_by_total(self.progress["total"])["file"])
        comp = compose_on_bg(img).convert("RGB")
        lvl = level_by_total(self.progress["total"])
        caption = f"{lvl['label']} • Очков: {self.progress['total']:.1f}"
        if self.progress.get("mood") == "sad":
            caption = f"Кот грустит 😿 • Очков: {self.progress['total']:.1f}"
        self._draw_caption(comp, caption)
        self._imgtk_cache = ImageTk.PhotoImage(comp)
        self.image_lbl.configure(image=self._imgtk_cache)

    def disable_controls(self, disabled: bool):
        state = "disabled" if disabled else "normal"
        for w in (self.focus_cb, self.sessions_cb, self.break_cb):
            w.configure(state=state)
        self.start_btn.configure(state=("disabled" if disabled else "normal"))
        self.finish_btn.configure(state=("normal" if disabled else "disabled"))

    def animate_sequence(self, name: str, delay_ms: int = 280):
        seq = [p for p in CAT_IMAGES.get(name, []) if p.exists()]
        if not seq: return
        def step(i=0):
            if i >= len(seq): return
            frame = open_rgba(seq[i])
            comp = compose_on_bg(frame).convert("RGB")
            self._imgtk_cache = ImageTk.PhotoImage(comp)
            self.image_lbl.configure(image=self._imgtk_cache)
            self.root.after(delay_ms, step, i+1)
        step(0)

    def on_start(self):
        if self.state != "idle": return
        try: self.focus_len = float(self.focus_cb.get())
        except Exception: self.focus_len = 25.0
        try: self.total_cycles = int(self.sessions_cb.get())
        except Exception: self.total_cycles = 1
        try: self.break_len = float(self.break_cb.get())
        except Exception: self.break_len = 5.0

        self.current_cycle = 1
        self.state = "focusing"
        self.end_ts = time.time() + self.focus_len * 60.0
        self.set_message(f"Сессия 1 из {self.total_cycles} началась. Удачи! 💪")
        self.cycle_lbl.configure(text=f"Цикл: {self.current_cycle}/{self.total_cycles}")
        self.disable_controls(True)
        self.animate_sequence("study_intermediate")
        self.animate_sequence("study")

    def on_finish(self):
        if self.state in ("focusing","break"):
            self.state = "idle"
            self.end_ts = None
            self.current_cycle = 0
            self.progress["mood"] = "sad"
            save_progress(self.progress)
            self.set_message("Сессия прервана — очки не начислены. Кот грустит 😿", color="#e53935")
            self.timer_lbl.configure(text="00:00")
            self.update_cat_image()
            self.disable_controls(False)
            self.animate_sequence("to_neutral")
            self.animate_sequence("sleep_intermediate")

    def tick(self):
        now = time.time()
        if self.state in ("focusing","break") and self.end_ts:
            remaining = self.end_ts - now
            self.timer_lbl.configure(text=format_mmss(remaining))
            if remaining <= 0:
                if self.state == "focusing":
                    gained = self.focus_len * POINTS_PER_MIN
                    self.progress["total"] = float(self.progress["total"]) + float(gained)
                    lvl = level_by_total(self.progress["total"])
                    self.progress["level"] = lvl["name"]
                    self.progress["last_session"] = datetime.now().isoformat(timespec="seconds")
                    self.progress["mood"] = "normal"
                    save_progress(self.progress)

                    self.points_val.configure(text=f"{self.progress['total']:.1f}")
                    self.level_val.configure(text=self.progress["level"])
                    self.update_cat_image()

                    if self.current_cycle < self.total_cycles:
                        self.state = "break"
                        self.end_ts = time.time() + self.break_len * 60.0
                        self.set_message(f"🎉 Сессия {self.current_cycle} завершена (+{gained:.1f}). Перерыв {self.break_len:g} мин.")
                        self.animate_sequence("to_sleep")
                        self.animate_sequence("sleep_intermediate")
                        self.animate_sequence("sleep")
                    else:
                        self.state = "idle"
                        self.end_ts = None
                        self.current_cycle = 0
                        self.set_message(f"🎉 Все {self.total_cycles} сессий завершены. +{gained:.1f} за последнюю.")
                        self.timer_lbl.configure(text="00:00")
                        self.disable_controls(False)
                        self.animate_sequence("to_happy")
                        self.animate_sequence("happy_intermediate")
                        self.animate_sequence("happy")
                elif self.state == "break":
                    self.current_cycle += 1
                    self.state = "focusing"
                    self.end_ts = time.time() + self.focus_len * 60.0
                    self.set_message(f"Сессия {self.current_cycle} из {self.total_cycles} началась. Поехали! 💪")
                    self.cycle_lbl.configure(text=f"Цикл: {self.current_cycle}/{self.total_cycles}")
                    self.animate_sequence("study_intermediate")
                    self.animate_sequence("study")
        self.root.after(200, self.tick)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    App().run()
