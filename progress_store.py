# progress_store.py
# Selles failis on kassi progressi (punktid/tase/tuju) lugemine ja salvestamine.

from __future__ import annotations

import json
from typing import Dict

import config as cfg

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
        raw = cfg.PROGRESS_PATH.read_text(encoding="utf-8") if cfg.PROGRESS_PATH.exists() else "{}"
        data = json.loads(raw or "{}")
    except Exception:
        data = {}

    progress: Dict[str, object] = {**defaults, **data}

    try:
        progress["total"] = float(progress["total"])  # type: ignore[assignment]
    except Exception:
        progress["total"] = 0.0

    if progress["stage"] not in cfg.STAGES:
        progress["stage"] = "baby"
    if progress["mood"] not in cfg.MOODS:
        progress["mood"] = "sad"

    save_progress(progress)
    return progress

def save_progress(progress: Dict[str, object]) -> None:
    """Salvestab kassi seisu progress.json-faili."""
    cfg.PROGRESS_PATH.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
