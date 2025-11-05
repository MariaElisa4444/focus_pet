import json, time
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
import streamlit as st

# ---------- Пути ----------
ROOT = Path(__file__).parent
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"
SPRITES = ASSETS / "sprites"
UI = ASSETS / "ui"
PROGRESS = DATA / "progress.json"

# ---------- Параметры ----------
FOCUS_CHOICES = [0.1, 1, 5, 10, 15, 20, 25, 30, 40, 45, 50, 60]
SESSIONS_CHOICES = list(range(1, 9))            # 1..8
BREAK_CHOICES = [0.1, 1, 2, 3, 5, 7, 10, 15, 20, 25]
POINTS_PER_MIN = 1
LEVELS = [
    {"min_total": 0,   "name": "baby",  "file": "baby.png",  "label": "Baby"},
    {"min_total": 0.3, "name": "teen",  "file": "teen.png",  "label": "Teen"},
    {"min_total": 0.5, "name": "adult", "file": "adult.png", "label": "Adult"},
]
SAD_FILE = "sad.png"
BG_FILE = (UI / "bg.png") if (UI / "bg.png").exists() else None

# ---------- Утилиты ----------
def load_progress():
    if PROGRESS.exists():
        try:
            p = json.loads(PROGRESS.read_text(encoding="utf-8"))
            # обратная совместимость: если нет mood — добавим
            if "mood" not in p:
                p["mood"] = "normal"
            return p
        except Exception:
            pass
    # дефолт
    data = {"total": 0, "level": "baby", "last_session": None, "mood": "normal"}
    save_progress(data); return data

def save_progress(p):
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

def level_by_total(total):
    lvl = LEVELS[0]
    for x in LEVELS:
        if total >= x["min_total"]:
            lvl = x
    return lvl

def format_mmss(sec: int):
    m, s = divmod(int(max(0, sec)), 60)
    return f"{m:02d}:{s:02d}"

# ---------- Оформление ----------
st.set_page_config(page_title="Focus Pet — Cycles", page_icon="🐾", layout="centered")
if BG_FILE:
    bg = BG_FILE.as_posix()
    st.markdown(f"""
    <style>
    .stApp {{ background: url('{bg}') center/cover fixed no-repeat; }}
    .timer {{ font-size:64px; font-weight:800; text-align:center; letter-spacing:2px;
              background: rgba(255,255,255,0.85); padding:12px 18px; border-radius:16px; }}
    .panel {{ background: rgba(255,255,255,0.85); padding:16px; border-radius:16px;
              box-shadow:0 10px 30px rgba(0,0,0,0.08); }}
    </style>
    """, unsafe_allow_html=True)

# ---------- Состояние ----------
if "progress" not in st.session_state:
    st.session_state.progress = load_progress()
if "state" not in st.session_state:
    st.session_state.state = "idle"   # idle|focusing|break
if "end_time" not in st.session_state:
    st.session_state.end_time = None
if "focus_len" not in st.session_state:
    st.session_state.focus_len = 25
if "break_len" not in st.session_state:
    st.session_state.break_len = 5
if "total_cycles" not in st.session_state:
    st.session_state.total_cycles = 1
if "current_cycle" not in st.session_state:
    st.session_state.current_cycle = 0
if "message" not in st.session_state:
    st.session_state.message = ""

progress = st.session_state.progress
current_lvl = level_by_total(progress["total"])

# ---------- UI ----------
st.title("🐾 Focus Pet — циклы фокуса и перерывов")

col1, col2 = st.columns([1,1], gap="large")

with col1:
    st.subheader("Питомец")
    # если настроение sad — показываем грустного КОТА до успешного завершения следующей фокус-сессии
    if progress.get("mood", "normal") == "sad":
        sprite_file = SAD_FILE
        caption = f"Кот грустит 😿 • Очков: {progress['total']}"
    else:
        sprite_file = current_lvl["file"]
        caption = f"Уровень: {current_lvl['label']} • Очков: {progress['total']}"
    img = Image.open(SPRITES / sprite_file)
    st.image(img, use_container_width=True, caption=caption)

with col2:
    st.subheader("Параметры сессий")
    disabled_controls = st.session_state.state in ("focusing", "break")
    st.session_state.focus_len = st.selectbox(
        "⏱️ Длительность фокуса (мин)",
        FOCUS_CHOICES, index=FOCUS_CHOICES.index(st.session_state.focus_len),
        disabled=disabled_controls
    )
    st.session_state.total_cycles = st.selectbox(
        "🔁 Кол-во сессий",
        SESSIONS_CHOICES, index=SESSIONS_CHOICES.index(st.session_state.total_cycles),
        disabled=disabled_controls
    )
    if st.session_state.total_cycles > 1:
        # выбор перерыва только когда есть несколько сессий
        default_idx = BREAK_CHOICES.index(st.session_state.break_len) if st.session_state.break_len in BREAK_CHOICES else 2
        st.session_state.break_len = st.selectbox(
            "🍵 Перерыв между сессиями (мин)",
            BREAK_CHOICES, index=max(0, default_idx),
            disabled=disabled_controls
        )
    else:
        st.info("Перерыв не нужен — сессия одна.", icon="ℹ️")

    st.subheader("Управление")
    c1, c2 = st.columns(2)
    with c1:
        start_clicked = st.button(
            "▶️ Start",
            use_container_width=True,
            disabled=st.session_state.state in ("focusing","break")
        )
    with c2:
        finish_clicked = st.button(
            "⏹️ Finish",
            use_container_width=True,
            disabled=st.session_state.state == "idle"
        )

    st.markdown("---")
    st.write(f"Цикл: **{st.session_state.current_cycle}/{st.session_state.total_cycles}**")
    timer_box = st.empty()
    msg_box = st.empty()

# ---------- Helpers ----------
def reset_to_idle(msg=""):
    st.session_state.state = "idle"
    st.session_state.end_time = None
    st.session_state.current_cycle = 0
    st.session_state.message = msg

# ---------- Start ----------
if start_clicked and st.session_state.state == "idle":
    st.session_state.current_cycle = 1
    st.session_state.state = "focusing"
    st.session_state.end_time = datetime.now() + timedelta(minutes=st.session_state.focus_len)
    st.session_state.message = f"Сессия 1 из {st.session_state.total_cycles} началась. Удачи! 💪"
    st.rerun()

# ---------- Finish (досрочно = делает кота грустным до следующей успешной сессии) ----------
if finish_clicked and st.session_state.state in ("focusing","break"):
    # Прерываем весь цикл
    st.session_state.end_time = None
    st.session_state.state = "idle"
    st.session_state.current_cycle = 0
    st.session_state.message = "Сессия прервана — очки не начислены. Кот грустит 😿"

    # ВАЖНО: зафиксируем грусть в progress, чтобы она сохранялась до следующего успеха (и между запусками)
    progress["mood"] = "sad"
    save_progress(progress)

    timer_box.markdown(f"<div class='timer'>00:00</div>", unsafe_allow_html=True)
    msg_box.warning(st.session_state.message)
    st.rerun()

# ---------- Таймерный цикл ----------
def tick_loop():
    while st.session_state.state in ("focusing","break") and st.session_state.end_time:
        remaining = (st.session_state.end_time - datetime.now()).total_seconds()

        if remaining <= 0:
            if st.session_state.state == "focusing":
                # Успешное завершение фокус-сессии -> начисляем очки
                gained = st.session_state.focus_len * POINTS_PER_MIN
                progress["total"] += gained
                new_lvl = level_by_total(progress["total"])
                progress["level"] = new_lvl["name"]
                progress["last_session"] = datetime.now().isoformat(timespec="seconds")

                # Снимаем грусть ТОЛЬКО при успешной фокус-сессии
                progress["mood"] = "normal"
                save_progress(progress)

                # Переход: либо перерыв, либо завершение всех циклов
                if st.session_state.current_cycle < st.session_state.total_cycles:
                    st.session_state.state = "break"
                    st.session_state.end_time = datetime.now() + timedelta(minutes=st.session_state.break_len)
                    st.session_state.message = (
                        f"🎉 Сессия {st.session_state.current_cycle} завершена (+{gained} очков). "
                        f"Перерыв {st.session_state.break_len} мин 🍵"
                    )
                    st.rerun()
                else:
                    msg = f"🎉 Все {st.session_state.total_cycles} сессий завершены. +{gained} очков за последнюю."
                    reset_to_idle(msg)
                    st.rerun()

            elif st.session_state.state == "break":
                # Перерыв завершён -> следующая фокус-сессия
                st.session_state.current_cycle += 1
                st.session_state.state = "focusing"
                st.session_state.end_time = datetime.now() + timedelta(minutes=st.session_state.focus_len)
                st.session_state.message = f"Сессия {st.session_state.current_cycle} из {st.session_state.total_cycles} началась. Поехали! 💪"
                st.rerun()

        timer_box.markdown(f"<div class='timer'>{format_mmss(int(remaining))}</div>", unsafe_allow_html=True)
        msg_box.info(st.session_state.message)
        time.sleep(1)

# Запускаем тик, если идёт фокус или перерыв
if st.session_state.state in ("focusing","break") and st.session_state.end_time:
    tick_loop()
else:
    timer_box.markdown(f"<div class='timer'>00:00</div>", unsafe_allow_html=True)
    if st.session_state.message:
        msg_box.info(st.session_state.message)