"""
Stem Separator for MixBot

Separates audio into stems (vocals, drums, bass, other) and analyzes each one.

Strategy (in priority order):
  1. Demucs (deep learning) — best quality, requires torch + demucs installed
  2. librosa HPSS + band filtering — always available, good approximation

The StemSeparator class is a context manager that cleans up temp files on exit.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

import numpy as np
import librosa
import soundfile as sf


# ── Demucs availability check ─────────────────────────────────────────────────

_DEMUCS_AVAILABLE = False
try:
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    _DEMUCS_AVAILABLE = True
except ImportError:
    pass


# ── Main class ────────────────────────────────────────────────────────────────

class StemSeparator:
    """
    Context manager for stem separation and per-stem analysis.

    Usage:
        with StemSeparator(stems=4) as sep:
            paths = sep.separate_audio("/path/to/track.wav")
            for name, path in paths.items():
                metrics = sep.analyze_stem(path, name)
    """

    STEM_NAMES_4 = ["vocals", "drums", "bass", "other"]
    STEM_NAMES_2 = ["vocals", "accompaniment"]

    def __init__(self, stems: int = 4):
        self.stems = stems
        self._temp_files: list[str] = []

    def __enter__(self) -> "StemSeparator":
        return self

    def __exit__(self, *args) -> None:
        for path in self._temp_files:
            try:
                os.unlink(path)
            except Exception:
                pass
        self._temp_files.clear()

    def _make_temp_wav(self, audio: np.ndarray, sr: int, suffix: str = "") -> str:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f"_{suffix}.wav"
        ) as f:
            path = f.name
        sf.write(path, audio, sr)
        self._temp_files.append(path)
        return path

    # ── Public API ────────────────────────────────────────────────────────────

    def separate_audio(self, file_path: str) -> dict[str, str]:
        """
        Separate audio into stems. Returns {stem_name: temp_file_path}.
        Uses Demucs if available, otherwise falls back to librosa approximation.
        """
        if _DEMUCS_AVAILABLE:
            try:
                return self._separate_demucs(file_path)
            except Exception:
                pass  # fall through to librosa
        return self._separate_librosa(file_path)

    def analyze_stem(self, stem_path: str, stem_name: str) -> dict:
        """
        Analyze a single stem file and return relevant metrics.
        Metrics vary by stem type to match what the UI displays.
        """
        try:
            audio, sr = librosa.load(stem_path, sr=None)
        except Exception as e:
            return {"error": str(e)}

        base = self._base_metrics(audio, sr)

        if stem_name == "vocals":
            return {**base, **self._vocal_metrics(audio, sr)}
        elif stem_name == "bass":
            return {**base, **self._bass_metrics(audio, sr)}
        elif stem_name == "drums":
            return {**base, **self._drum_metrics(audio, sr)}
        else:
            return {**base, **self._other_metrics(audio, sr)}

    # ── Separation backends ───────────────────────────────────────────────────

    def _separate_demucs(self, file_path: str) -> dict[str, str]:
        """Use Demucs htdemucs model for high-quality separation."""
        model = get_model("htdemucs")
        model.eval()

        audio, sr = librosa.load(file_path, sr=model.samplerate, mono=False)
        if audio.ndim == 1:
            audio = np.stack([audio, audio])

        wav = torch.tensor(audio).unsqueeze(0).float()
        with torch.no_grad():
            sources = apply_model(model, wav, device="cpu")[0]

        stem_names = model.sources  # ["drums", "bass", "other", "vocals"]
        paths = {}
        for i, name in enumerate(stem_names):
            stem_audio = sources[i].mean(0).numpy()
            paths[name] = self._make_temp_wav(stem_audio, model.samplerate, name)

        return paths

    def _separate_librosa(self, file_path: str) -> dict[str, str]:
        """
        Librosa-based approximation when Demucs is not available.
        Uses harmonic-percussive separation + frequency band filtering.
        """
        audio, sr = librosa.load(file_path, sr=None)

        # Harmonic/percussive split
        harmonic, percussive = librosa.effects.hpss(audio, margin=3.0)

        # Bass: low-pass filter on harmonic content (< 300 Hz)
        bass = self._bandpass(harmonic, sr, lo=20, hi=300)

        # Vocals: bandpass on harmonic content (250 Hz – 4 kHz)
        vocals = self._bandpass(harmonic, sr, lo=250, hi=4000)

        # Drums: percussive content
        drums = percussive

        # Other: harmonic minus vocals and bass (residual)
        other = harmonic - vocals - bass
        other = np.clip(other, -1.0, 1.0)

        return {
            "vocals": self._make_temp_wav(vocals, sr, "vocals"),
            "bass": self._make_temp_wav(bass, sr, "bass"),
            "drums": self._make_temp_wav(drums, sr, "drums"),
            "other": self._make_temp_wav(other, sr, "other"),
        }

    # ── Signal processing helpers ─────────────────────────────────────────────

    @staticmethod
    def _bandpass(audio: np.ndarray, sr: int, lo: float, hi: float) -> np.ndarray:
        """Simple FFT-based band-pass filter."""
        fft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(len(audio), d=1.0 / sr)
        mask = (freqs >= lo) & (freqs <= hi)
        fft_filtered = fft * mask
        return np.fft.irfft(fft_filtered, n=len(audio))

    @staticmethod
    def _rms_db(audio: np.ndarray) -> float:
        rms = np.sqrt(np.mean(audio ** 2))
        return float(20 * np.log10(rms)) if rms > 1e-9 else -96.0

    @staticmethod
    def _peak_db(audio: np.ndarray) -> float:
        peak = np.max(np.abs(audio))
        return float(20 * np.log10(peak)) if peak > 1e-9 else -96.0

    def _base_metrics(self, audio: np.ndarray, sr: int) -> dict:
        rms = self._rms_db(audio)
        peak = self._peak_db(audio)
        return {
            "rms_db": round(rms, 2),
            "peak_db": round(peak, 2),
            "dynamic_range": round(peak - rms, 2),
        }

    # ── Per-stem metrics ──────────────────────────────────────────────────────

    def _vocal_metrics(self, audio: np.ndarray, sr: int) -> dict:
        # Vocal clarity: spectral centroid in the voice range (300–3500 Hz)
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr)))
        vocal_clarity = round(
            np.clip((centroid - 300) / (3500 - 300), 0, 1), 3
        )

        # Sibilance: energy ratio 5–10 kHz
        stft = np.abs(librosa.stft(audio))
        freqs = librosa.fft_frequencies(sr=sr)
        sib_mask = (freqs >= 5000) & (freqs <= 10000)
        total_energy = np.sum(stft) + 1e-9
        sibilance = round(float(np.sum(stft[sib_mask])) / total_energy, 3)

        # Pitch range via pyin
        try:
            f0, voiced_flag, _ = librosa.pyin(
                audio, fmin=80, fmax=1200,
                sr=sr, frame_length=2048
            )
            voiced = f0[voiced_flag] if voiced_flag is not None else np.array([])
            if len(voiced) > 0:
                pitch_range = {
                    "min_pitch": round(float(np.percentile(voiced, 5)), 1),
                    "max_pitch": round(float(np.percentile(voiced, 95)), 1),
                }
            else:
                pitch_range = {"min_pitch": 0.0, "max_pitch": 0.0}
        except Exception:
            pitch_range = {"min_pitch": 0.0, "max_pitch": 0.0}

        return {
            "vocal_clarity": vocal_clarity,
            "sibilance": sibilance,
            "pitch_range": pitch_range,
        }

    def _bass_metrics(self, audio: np.ndarray, sr: int) -> dict:
        stft = np.abs(librosa.stft(audio))
        freqs = librosa.fft_frequencies(sr=sr)
        total_energy = np.sum(stft) + 1e-9

        sub_mask = freqs < 80
        bass_mask = (freqs >= 80) & (freqs < 250)

        sub_bass = round(float(np.sum(stft[sub_mask])) / total_energy, 3)
        bass_weight = round(
            float(np.sum(stft[sub_mask]) + np.sum(stft[bass_mask])) / total_energy, 3
        )

        centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr)))
        bass_clarity = round(np.clip(1.0 - centroid / 500, 0, 1), 3)

        return {
            "bass_weight": bass_weight,
            "bass_clarity": bass_clarity,
            "sub_bass": sub_bass,
        }

    def _drum_metrics(self, audio: np.ndarray, sr: int) -> dict:
        stft = np.abs(librosa.stft(audio))
        freqs = librosa.fft_frequencies(sr=sr)
        total_energy = np.sum(stft) + 1e-9

        # Kick punch: energy in 50–120 Hz (kick drum fundamental)
        kick_mask = (freqs >= 50) & (freqs <= 120)
        kick_punch = round(float(np.sum(stft[kick_mask])) / total_energy, 3)

        # Snare presence: energy in 150–400 Hz + 3–8 kHz
        snare_mask = (
            ((freqs >= 150) & (freqs <= 400)) |
            ((freqs >= 3000) & (freqs <= 8000))
        )
        snare_presence = round(float(np.sum(stft[snare_mask])) / total_energy, 3)

        # Drum tightness: spectral flux (how fast energy changes)
        flux = librosa.onset.onset_strength(y=audio, sr=sr)
        drum_tightness = round(float(np.std(flux)) / (float(np.mean(flux)) + 1e-9), 3)
        drum_tightness = round(np.clip(drum_tightness, 0, 1), 3)

        return {
            "kick_punch": kick_punch,
            "snare_presence": snare_presence,
            "drum_tightness": drum_tightness,
        }

    def _other_metrics(self, audio: np.ndarray, sr: int) -> dict:
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr)))
        bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr)))
        harmonic, _ = librosa.effects.hpss(audio)
        harmonic_ratio = round(
            float(np.sqrt(np.mean(harmonic ** 2))) /
            (float(np.sqrt(np.mean(audio ** 2))) + 1e-9),
            3
        )
        return {
            "spectral_centroid_hz": round(centroid, 1),
            "spectral_bandwidth_hz": round(bandwidth, 1),
            "harmonic_ratio": harmonic_ratio,
        }
