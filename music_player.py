# music_player.py
# See fail tegeleb ainult muusikaga (pygame.mixer)
# Siin on üks klass MusicPlayer, millele ütled: 
# - kas muusika on ON/OFF
# - kas olek on focusing / paused / stop
# - iga ticki ajal kontrollime, kas lugu sai läbi

from __future__ import annotations # võimaldab kirjutada tüübimärkusi vabamalt, isegi kui vastav klass on failis allpool

from pathlib import Path
from typing import List, Optional

class MusicPlayer:
    """
    MusicPlayer hoiab muusika loogika eraldi.
    Ta oskab:
    - leida track1.mp3, track2.mp3 ... assets/music kaustast
    - mängida neid JÄRJEKORRAS
    - kui jõuab lõppu, läheb uuesti algusesse (loop)
    - OFF -> stop, ON -> mängib ainult focusing ajal
    - pause/resume töötab
    """

    def __init__(
        self,
        assets_path: Path,
        pygame_module,
        volume: float = 0.4,
        max_tracks: int = 50,
    ) -> None:
        # salvestame teed ja pygame mooduli
        self.assets_path = assets_path
        self.pygame = pygame_module

        # helitugevus (0.0 kuni 1.0)
        self.volume = volume

        # kas kasutaja on valinud Music: ON (True) või OFF (False)
        self.enabled: bool = False

        # kas meil on üldse võimalik muusikat mängida (pygame + failid)
        self.available: bool = False

        # siia kogume kõik leitud trackid
        self.tracks: List[Path] = []

        # mis indeksiga lugu mängib (alustame -1)
        self.current_index: int = -1

        # tracki proovime otsida (track1..trackN)
        self.max_tracks = max_tracks

        # käivitame initsi kohe ära
        self._init()

    def _init(self) -> None:
        """Proovib pygame.mixer init + leiab trackid."""
        if self.pygame is None:
            self.available = False
            return

        music_folder = self.assets_path / "music"
        found: List[Path] = []

        # otsime järjest track1.mp3, track2.mp3 jne
        for i in range(1, self.max_tracks + 1):
            p = music_folder / f"track{i}.mp3"
            if p.exists():
                found.append(p)

        if not found:
            self.available = False
            return

        self.tracks = found
        self.current_index = -1

        try:
            self.pygame.mixer.init()
            self.pygame.mixer.music.set_volume(self.volume)
            self.available = True
        except Exception:
            self.available = False

    # API mida põhiprogramm kasutab

    def handle_toggle(self, value: str) -> None:
        """
        Seda kutsub SideMenu.
        value on tavaliselt "on" või "off" (teeme kindlalt lower()).
        """
        v = (value or "").strip().lower()
        self.enabled = (v == "on")

        if not self.enabled:
            # kui OFF, siis peatame kohe
            self.stop()

    def start_for_focusing(self) -> None:
        """
        Focusing alguses kutsu seda.
        Kui enabled + available, siis hakkab mängima (või jätkab).
        """
        if not self.available or not self.enabled:
            return
        if self.pygame is None:
            return

        try:
            # kui juba mängib, siis ära tee midagi
            if self.pygame.mixer.music.get_busy():
                return
        except Exception:
            # kui get_busy error, proovime lihtsalt järgmise käima panna
            pass

        self.play_next()

    def pause(self) -> None:
        """Paneb muusika pausile."""
        if not self.available or self.pygame is None:
            return
        try:
            self.pygame.mixer.music.pause()
        except Exception:
            pass

    def unpause(self) -> None:
        """Võtab pausi maha."""
        if not self.available or not self.enabled or self.pygame is None:
            return
        try:
            self.pygame.mixer.music.unpause()
        except Exception:
            pass

    def stop(self) -> None:
        """Peatab muusika täiesti."""
        if not self.available or self.pygame is None:
            return
        try:
            self.pygame.mixer.music.stop()
        except Exception:
            pass

    def play_next(self) -> None:
        """Mängib järgmise loo järjekorras (ja teeb ringi lõpus)."""
        if not self.available or not self.enabled:
            return
        if self.pygame is None or not self.tracks:
            return

        self.current_index = (self.current_index + 1) % len(self.tracks)
        track_path = self.tracks[self.current_index]

        try:
            self.pygame.mixer.music.load(str(track_path))
            self.pygame.mixer.music.play()
        except Exception:
            # kui üks fail ei tööta, proovime järgmise
            try:
                self.pygame.mixer.music.stop()
            except Exception:
                pass

    def tick(self, is_focusing: bool) -> None:
        """
        Kutsu iga _tick() lõpus.
        Kui focusing + enabled, siis kontrollime:
        - kui lugu sai läbi -> järgmine
        """
        if not self.available or not self.enabled:
            return
        if not is_focusing:
            return
        if self.pygame is None:
            return

        try:
            if not self.pygame.mixer.music.get_busy():
                self.play_next()
        except Exception:
            pass
