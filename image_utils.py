# image_utils.py
# Selles failis on piltide ja aja kuvamise abifunktsioonid.

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import Image, ImageTk

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
