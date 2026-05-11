"""
Shared audio analysis helpers used by both the MCP server and the AI agent.

Returns plain dicts so results are easily serializable to JSON.
"""

from __future__ import annotations

import numpy as np
import librosa
import soundfile as sf
from typing import Optional


def analyze_audio_file(file_path: str) -> dict:
    """
    Full audio analysis: duration, loudness, tempo, clipping, silence.

    Returns a dict with all metrics.
    """
    try:
        audio, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        return {"error": f"Could not load audio: {e}"}

    duration = len(audio) / sr
    rms_linear = float(np.sqrt(np.mean(audio ** 2)))
    rms_db = float(20 * np.log10(rms_linear)) if rms_linear > 0 else -96.0

    peak_linear = float(np.max(np.abs(audio)))
    peak_db = float(20 * np.log10(peak_linear)) if peak_linear > 0 else -96.0

    # Clipping
    flat_peaks = int(np.sum(np.abs(audio) > 0.99))
    flat_peak_ratio = flat_peaks / len(audio)
    is_clipped = peak_db > -0.1 or flat_peak_ratio > 0.001

    # Tempo
    try:
        tempo_arr, _ = librosa.beat.beat_track(y=audio, sr=sr)
        tempo = float(np.atleast_1d(tempo_arr)[0])
    except Exception:
        tempo = 0.0

    # Silence
    threshold_linear = 10 ** (-40.0 / 20.0)
    window_size = max(1, int(0.01 * sr))
    hop_size = max(1, window_size // 2)
    silence_count = 0
    for i in range(0, len(audio) - window_size, hop_size):
        if np.sqrt(np.mean(audio[i:i + window_size] ** 2)) < threshold_linear:
            silence_count += 1
    total_windows = max(1, (len(audio) - window_size) // hop_size)
    silence_percentage = (silence_count / total_windows) * 100

    dynamic_range = peak_db - rms_db

    return {
        "duration_seconds": round(duration, 2),
        "duration_minutes": round(duration / 60, 2),
        "sample_rate": int(sr),
        "rms_linear": round(rms_linear, 6),
        "rms_db": round(rms_db, 2),
        "peak_db": round(peak_db, 2),
        "dynamic_range_db": round(dynamic_range, 2),
        "tempo_bpm": round(tempo, 1),
        "is_clipped": bool(is_clipped),
        "silence_percentage": round(silence_percentage, 1),
    }


def get_spectral_features(file_path: str) -> dict:
    """
    Spectral analysis: centroid, bandwidth, rolloff, zero-crossing rate.
    Useful for frequency balance and tonal character assessment.
    """
    try:
        audio, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        return {"error": f"Could not load audio: {e}"}

    centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr)))
    bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=audio)))

    # Rough frequency band energy
    stft = np.abs(librosa.stft(audio))
    freqs = librosa.fft_frequencies(sr=sr)

    def band_energy(lo, hi):
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            return 0.0
        return float(np.mean(stft[mask]))

    return {
        "spectral_centroid_hz": round(centroid, 1),
        "spectral_bandwidth_hz": round(bandwidth, 1),
        "spectral_rolloff_hz": round(rolloff, 1),
        "zero_crossing_rate": round(zcr, 4),
        "sub_bass_energy": round(band_energy(20, 80), 4),
        "bass_energy": round(band_energy(80, 250), 4),
        "low_mid_energy": round(band_energy(250, 500), 4),
        "mid_energy": round(band_energy(500, 2000), 4),
        "high_mid_energy": round(band_energy(2000, 6000), 4),
        "air_energy": round(band_energy(6000, 20000), 4),
    }


def get_mix_recommendations(
    metrics: dict,
    daw: str = "",
    genre: str = "",
) -> dict:
    """
    Rule-based recommendations derived from analysis metrics.
    Returns a structured dict of issues and suggested fixes.
    """
    issues = []
    suggestions = []

    rms = metrics.get("rms_db", -20)
    peak = metrics.get("peak_db", -1)
    dr = metrics.get("dynamic_range_db", 10)
    clipped = metrics.get("is_clipped", False)
    tempo = metrics.get("tempo_bpm", 120)
    silence = metrics.get("silence_percentage", 0)

    if clipped:
        issues.append("CLIPPING DETECTED — reduce master fader by 3-5 dB immediately")

    if rms > -8:
        issues.append(f"RMS too hot ({rms} dB) — risk of over-limiting")
        suggestions.append("Lower master fader 2-3 dB before mastering")
    elif rms < -18:
        suggestions.append("RMS is low — gentle bus compression can raise perceived loudness")

    if dr < 6:
        issues.append(f"Very low dynamic range ({dr} dB) — mix sounds crushed")
        suggestions.append("Back off limiting/compression to restore punch")
    elif dr > 18:
        suggestions.append("Large dynamic range — consider gentle bus compression for cohesion")

    if silence > 15:
        suggestions.append(f"High silence ({silence}%) — check for unintended gaps")

    if tempo > 0:
        if tempo < 75:
            suggestions.append("Slow tempo — focus on groove; subtle swing can help feel")
        elif tempo > 165:
            suggestions.append("Fast tempo — prioritise clarity; side-chain can create space")

    daw_note = f"Targeted for {daw}." if daw else ""
    genre_note = f"Genre context: {genre}." if genre else ""

    return {
        "issues": issues,
        "suggestions": suggestions,
        "daw": daw,
        "genre": genre,
        "summary": f"{daw_note} {genre_note} {len(issues)} issue(s) found.".strip(),
    }
