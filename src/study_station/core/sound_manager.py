"""Calm audio cues and feedback manager for Study Station.

Provides subtle, soothing acoustic feedback for session completions:
- Synthesizes a high-purity, harmonic two-layer chime (C5 + E5 + G5 with exponential decay)
- Zero external audio binary dependencies (pure Python wave + struct)
- Non-blocking asynchronous playback across Windows, Linux (PipeWire / PulseAudio / ALSA), and macOS
- Safe fallbacks for headless CI and systems without sound cards
"""

from __future__ import annotations
import math
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import threading
import wave


class SoundManager:
    """Manages playback of calm acoustic cues and completion chimes."""

    _instance: SoundManager | None = None
    _sound_dir: Path | None = None

    def __init__(self, sound_dir: Path | None = None) -> None:
        if sound_dir:
            self.sound_dir = sound_dir
        else:
            from study_station.core.resources import get_writable_sound_dir
            self.sound_dir = get_writable_sound_dir()
        self.sound_dir.mkdir(parents=True, exist_ok=True)
        self.chime_path = self.sound_dir / "completion_chime.wav"
        self._ensure_chime_asset()
        self.last_played_file: str | None = None

    @classmethod
    def get_instance(cls) -> SoundManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_chime_asset(self) -> None:
        """Synthesize harmonic completion chime if not already present on disk."""
        if self.chime_path.exists() and self.chime_path.stat().st_size > 1000:
            return

        sample_rate = 44100
        duration = 1.4  # seconds
        num_samples = int(sample_rate * duration)

        samples: list[int] = []
        for i in range(num_samples):
            t = i / sample_rate

            # 15ms smooth attack envelope to prevent onset click
            if t < 0.015:
                env_attack = t / 0.015
            else:
                env_attack = 1.0

            decay_fund = math.exp(-3.2 * t)
            decay_third = math.exp(-3.8 * t)
            decay_fifth = math.exp(-4.5 * t)
            decay_sparkle = math.exp(-6.0 * t)

            # Harmonic additive synthesis: C5 (523.25 Hz), E5 (659.25 Hz), G5 (783.99 Hz), C6 (1046.5 Hz)
            s = (
                0.50 * math.sin(2 * math.pi * 523.25 * t) * decay_fund
                + 0.32 * math.sin(2 * math.pi * 659.25 * t) * decay_third
                + 0.18 * math.sin(2 * math.pi * 783.99 * t) * decay_fifth
                + 0.08 * math.sin(2 * math.pi * 1046.50 * t) * decay_sparkle
            ) * env_attack

            # Scale to 16-bit signed integer
            sample_val = int(max(-32767, min(32767, s * 24000)))
            samples.append(sample_val)

        try:
            with wave.open(str(self.chime_path), "wb") as wav:
                wav.setnchannels(1)  # Mono
                wav.setsampwidth(2)  # 16-bit PCM
                wav.setframerate(sample_rate)
                raw_data = struct.pack(f"<{len(samples)}h", *samples)
                wav.writeframes(raw_data)
        except Exception:
            pass

    def play_completion_chime(self, enabled: bool = True) -> bool:
        """Play the calm focus completion chime if enabled.
        
        Runs asynchronously on a background thread to prevent any UI stutter.
        Returns True if playback was initiated, False if disabled or file missing.
        """
        if not enabled:
            return False

        if not self.chime_path.exists():
            self._ensure_chime_asset()

        if not self.chime_path.exists():
            return False

        self.last_played_file = str(self.chime_path)
        threading.Thread(target=self._play_file, args=(self.chime_path,), daemon=True).start()
        return True

    def _play_file(self, file_path: Path) -> None:
        """Play WAV audio file using the best available platform mechanism."""
        system = platform.system()

        # 1. Windows: Native winsound API
        if system == "Windows":
            try:
                import winsound
                winsound.PlaySound(str(file_path), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
                return
            except Exception:
                pass

        # 2. Linux: Standard PipeWire, PulseAudio, or ALSA players
        elif system == "Linux":
            for player in ("pw-play", "paplay", "aplay", "canberra-gtk-play"):
                player_bin = shutil.which(player)
                if player_bin:
                    try:
                        args = [player_bin]
                        if player == "canberra-gtk-play":
                            args.extend(["-f", str(file_path)])
                        else:
                            args.append(str(file_path))
                        subprocess.run(
                            args,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=3.0,
                            check=False,
                        )
                        return
                    except Exception:
                        continue

        # 3. macOS: Native afplay command
        elif system == "Darwin":
            afplay = shutil.which("afplay")
            if afplay:
                try:
                    subprocess.run(
                        [afplay, str(file_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3.0,
                        check=False,
                    )
                    return
                except Exception:
                    pass
