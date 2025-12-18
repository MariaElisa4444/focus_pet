# config.py
# Selles failis on projekti seaded ühes kohas (teed, valikud, pildid, tasemed).
# Eesmärk: focuspet.py jääb väiksemaks ja seadeid on lihtsam muuta.

from pathlib import Path
from typing import Dict

# Kaustade ja failide teed
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"
IMAGES = ASSETS / "images"
PROGRESS_PATH = DATA / "progress.json"

# Taimeri valikud
FOCUS_CHOICES = [0.1, 5, 10, 15, 20, 25, 30, 40, 45]               # minutites (0.1 testimiseks)
SESSIONS_CHOICES = [1, 2, 3]                               # mitu fookussessiooni järjest
BREAK_CHOICES = [0.1, 3, 5, 7, 10, 15]                         # paus minutites
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
