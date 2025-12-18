# timer.py
# Selles failis on taimeri loogika (olekumasin).


from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Literal


State = Literal["idle", "focusing", "break", "paused_focusing", "paused_break"]


@dataclass
class TimerEngine:
    """Taimeri olekumasin: hoiab aja- ja tsükliloogikat."""

    state: State = "idle"
    end_ts: Optional[float] = None
    paused_left: Optional[float] = None

    focus_len_min: float = 25.0
    break_len_min: float = 5.0

    total_cycles: int = 3
    current_cycle: int = 0

    def start(self, focus_min: float, break_min: float, cycles: int) -> None:
        """Käivitab fookussessiooni (lubatud idle või break olekus)."""
        if self.state not in ("idle", "break"):
            return

        self.focus_len_min = float(focus_min)
        self.break_len_min = float(break_min)

        c = int(cycles)
        self.total_cycles = c if c > 0 else 1

        if self.state == "idle":
            self.current_cycle = 1

        self.state = "focusing"
        self.end_ts = time.time() + self.focus_len_min * 60
        self.paused_left = None

    def pause_toggle(self) -> None:
        """Lülitab taimeri pausile või jätkab (PAUSE/RESUME)."""
        # 1) Paneme pausile
        if self.state in ("focusing", "break") and self.end_ts is not None:
            left = max(0.0, self.end_ts - time.time())
            self.paused_left = left
            self.end_ts = None

            if self.state == "focusing":
                self.state = "paused_focusing"
            else:
                self.state = "paused_break"
            return

        # 2) Jätkame pausilt
        if self.state in ("paused_focusing", "paused_break") and self.paused_left is not None:
            if self.state == "paused_focusing":
                self.state = "focusing"
            else:
                self.state = "break"

            self.end_ts = time.time() + self.paused_left
            self.paused_left = None

    def stop(self) -> None:
        """Tühistab sessiooni ja läheb idle olekusse."""
        self.state = "idle"
        self.end_ts = None
        self.paused_left = None
        self.current_cycle = 0

    def seconds_left(self) -> Optional[float]:
        """Tagastab, mitu sekundit on hetkel alles (focusing/break/paused)."""
        if self.state in ("focusing", "break") and self.end_ts is not None:
            return max(0.0, self.end_ts - time.time())

        if self.state in ("paused_focusing", "paused_break") and self.paused_left is not None:
            return max(0.0, self.paused_left)

        return None

    def hud_text(self) -> str:
        """Tekst HUD-i jaoks (Ready / Session x/y / Break / Paused)."""
        total = int(self.total_cycles) if self.total_cycles else 0
        cur = int(self.current_cycle) if self.current_cycle else 0

        if self.state == "focusing":
            return f"Session {cur}/{total}"
        if self.state == "break":
            return "Break"
        if self.state in ("paused_focusing", "paused_break"):
            return "Paused"
        return "Ready to start"

    def tick(self) -> Optional[str]:
        """
        Käivitatakse perioodiliselt.
        Kui midagi lõppes, tagastab sündmuse:
          - "focus_finished"
          - "break_finished"
          - "all_done"
        Muidu None.
        """
        if self.state not in ("focusing", "break") or self.end_ts is None:
            return None

        if (self.end_ts - time.time()) > 0:
            return None

        # Aeg sai läbi
        if self.state == "focusing":
            if self.current_cycle < self.total_cycles:
                self.state = "break"
                self.end_ts = time.time() + self.break_len_min * 60
                return "focus_finished"

            self.state = "idle"
            self.end_ts = None
            return "all_done"

        # break sai läbi -> uus focusing
        self.current_cycle += 1
        self.state = "focusing"
        self.end_ts = time.time() + self.focus_len_min * 60
        return "break_finished"
