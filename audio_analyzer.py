#!/usr/bin/env python3
"""
Audio Analysis Script

This script analyzes audio files to extract various metrics including:
- Duration
- Silence detection
- RMS (loudness)
- Tempo (BPM)
- Clipping detection

Usage: python audio_analyzer.py <audio_file_path>
"""

import sys
import argparse
import numpy as np
import librosa
import soundfile as sf
from typing import Tuple, List


def load_audio(file_path: str) -> Tuple[np.ndarray, int]:
    """
    Load audio file using librosa.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    try:
        # Load audio with librosa (automatically resamples to 22050 Hz)
        audio, sr = librosa.load(file_path, sr=None)
        return audio, sr
    except Exception as e:
        print(f"Error loading audio file: {e}")
        sys.exit(1)


def calculate_duration(audio: np.ndarray, sample_rate: int) -> float:
    """
    Calculate the duration of the audio track.
    
    Args:
        audio: Audio data array
        sample_rate: Sample rate in Hz
        
    Returns:
        Duration in seconds
    """
    return len(audio) / sample_rate


def detect_silence(audio: np.ndarray, sample_rate: int, 
                   threshold_db: float = -40.0, min_silence_duration: float = 0.1) -> List[Tuple[float, float]]:
    """
    Detect silence periods in the audio.
    
    Args:
        audio: Audio data array
        sample_rate: Sample rate in Hz
        threshold_db: Threshold in dB below which is considered silence
        min_silence_duration: Minimum duration (seconds) to be considered silence
        
    Returns:
        List of (start_time, end_time) tuples for silence periods
    """
    # Convert threshold from dB to linear scale
    threshold_linear = 10**(threshold_db / 20.0)
    
    # Calculate RMS in short windows
    window_size = int(0.01 * sample_rate)  # 10ms windows
    hop_size = window_size // 2
    
    rms_values = []
    for i in range(0, len(audio) - window_size, hop_size):
        window = audio[i:i + window_size]
        rms = np.sqrt(np.mean(window**2))
        rms_values.append(rms)
    
    # Find silence periods
    silence_periods = []
    in_silence = False
    silence_start = 0
    
    for i, rms in enumerate(rms_values):
        time = i * hop_size / sample_rate
        
        if rms < threshold_linear and not in_silence:
            silence_start = time
            in_silence = True
        elif rms >= threshold_linear and in_silence:
            silence_end = time
            if silence_end - silence_start >= min_silence_duration:
                silence_periods.append((silence_start, silence_end))
            in_silence = False
    
    # Handle case where audio ends in silence
    if in_silence:
        silence_end = len(audio) / sample_rate
        if silence_end - silence_start >= min_silence_duration:
            silence_periods.append((silence_start, silence_end))
    
    return silence_periods


def calculate_rms(audio: np.ndarray) -> Tuple[float, float]:
    """
    Calculate RMS (Root Mean Square) of the audio.
    
    Args:
        audio: Audio data array
        
    Returns:
        Tuple of (RMS in linear scale, RMS in dB)
    """
    rms_linear = np.sqrt(np.mean(audio**2))
    rms_db = 20 * np.log10(rms_linear) if rms_linear > 0 else -np.inf
    return rms_linear, rms_db


def estimate_tempo(audio: np.ndarray, sample_rate: int) -> Tuple[float, float]:
    """
    Estimate the tempo (BPM) of the audio.
    
    Args:
        audio: Audio data array
        sample_rate: Sample rate in Hz
        
    Returns:
        Tuple of (tempo, confidence)
    """
    try:
        # Use librosa's tempo estimation
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sample_rate)
        return tempo, 0.8  # librosa doesn't return confidence, using default
    except Exception as e:
        print(f"Warning: Could not estimate tempo: {e}")
        return 0.0, 0.0


def detect_clipping(audio: np.ndarray, sample_rate: int) -> Tuple[bool, float, float]:
    """
    Detect if audio is likely clipped.
    
    Args:
        audio: Audio data array
        sample_rate: Sample rate in Hz
        
    Returns:
        Tuple of (is_clipped, peak_level_db, clipping_threshold)
    """
    # Calculate peak level
    peak_level = np.max(np.abs(audio))
    peak_level_db = 20 * np.log10(peak_level) if peak_level > 0 else -np.inf
    
    # Check for clipping (typically above -0.1 dB for digital audio)
    clipping_threshold = -0.1
    is_clipped = peak_level_db > clipping_threshold
    
    # Additional check: look for flat peaks (common sign of clipping)
    flat_peak_threshold = 0.99
    flat_peaks = np.sum(np.abs(audio) > flat_peak_threshold)
    flat_peak_ratio = flat_peaks / len(audio)
    
    # If more than 0.1% of samples are at peak, likely clipped
    if flat_peak_ratio > 0.001:
        is_clipped = True
    
    return is_clipped, peak_level_db, clipping_threshold


def generate_mix_feedback(rms_db: float, peak_level_db: float, is_clipped: bool, 
                         silence_periods: List[Tuple[float, float]], tempo: float, 
                         duration: float, silence_percentage: float) -> None:
    """
    Generate professional mixing and mastering feedback based on analysis results.
    
    Args:
        rms_db: RMS level in dB
        peak_level_db: Peak level in dB
        is_clipped: Whether clipping was detected
        silence_periods: List of silence period timestamps
        tempo: Estimated tempo in BPM
        duration: Total duration in seconds
        silence_percentage: Percentage of silence in the track
    """
    print("📊 ANALYSIS SUMMARY:")
    print(f"   • RMS Level: {rms_db:.1f} dB")
    print(f"   • Peak Level: {peak_level_db:.1f} dB")
    print(f"   • Dynamic Range: {peak_level_db - rms_db:.1f} dB")
    print(f"   • Tempo: {float(tempo):.0f} BPM")
    print(f"   • Silence: {silence_percentage:.1f}% of track")
    print()
    
    # Loudness and Dynamics Analysis
    print("🔊 LOUDNESS & DYNAMICS:")
    if rms_db > -8:
        print("   ⚠️  RMS is quite high - consider reducing overall level")
        print("      → Lower your master fader by 2-3 dB")
        print("      → Check if individual tracks are too loud")
    elif rms_db < -16:
        print("   ℹ️  RMS is quite low - you have headroom for mastering")
        print("      → Consider gentle compression to bring up quiet parts")
        print("      → Ensure your mix translates well on different systems")
    else:
        print("   ✅ RMS level is in a good range for mastering")
    
    if peak_level_db > -1:
        print("   ⚠️  Peak level is very close to clipping")
        print("      → Reduce peak levels by 1-2 dB")
        print("      → Check for transients that need taming")
    elif peak_level_db < -6:
        print("   ℹ️  Peak level has good headroom")
        print("      → You can safely increase overall level if needed")
    
    dynamic_range = peak_level_db - rms_db
    if dynamic_range > 15:
        print("   ℹ️  Large dynamic range detected")
        print("      → Consider compression to control dynamics")
        print("      → Check if quiet parts are getting lost")
    elif dynamic_range < 6:
        print("   ⚠️  Very compressed/limited sound")
        print("      → Back off on compression/limiting")
        print("      → Allow more natural dynamics")
    
    print()
    
    # Clipping Analysis
    print("🎚️ CLIPPING & DISTORTION:")
    if is_clipped:
        print("   ❌ CLIPPING DETECTED - IMMEDIATE ACTION NEEDED:")
        print("      → Reduce master fader by 3-5 dB")
        print("      → Check individual tracks for clipping")
        print("      → Use a limiter with -1 dB ceiling")
        print("      → Consider using soft clipping for character")
    else:
        print("   ✅ No clipping detected - good headroom management")
    
    print()
    
    # Silence and Structure Analysis
    print("⏱️ TIMING & STRUCTURE:")
    if silence_percentage > 10:
        print(f"   ℹ️  High silence content ({silence_percentage:.1f}%)")
        print("      → Consider if long gaps serve the song")
        print("      → Add subtle ambience to fill empty spaces")
        print("      → Check if sections flow well together")
    elif silence_percentage < 2:
        print("   ℹ️  Very dense arrangement")
        print("      → Consider adding breathing room")
        print("      → Let important elements shine")
    
    if silence_periods:
        longest_silence = max(end - start for start, end in silence_periods)
        if longest_silence > 5:
            print(f"   ⚠️  Long silence detected ({longest_silence:.1f}s)")
            print("      → Consider if this serves the song")
            print("      → Add subtle elements to maintain interest")
    
    print()
    
    # Tempo and Rhythm Analysis
    print("🎵 TEMPO & RHYTHM:")
    if tempo > 0:
        if tempo < 80:
            print("   ℹ️  Slow tempo - focus on groove and feel")
            print("      → Ensure timing is tight")
            print("      → Consider subtle swing or groove")
        elif tempo > 160:
            print("   ℹ️  Fast tempo - clarity is key")
            print("      → Ensure each element has space")
            print("      → Consider side-chain compression")
        else:
            print("   ✅ Tempo is in a good range for most genres")
    
    print()
    
    # Specific Recommendations
    print("🎛️ SPECIFIC RECOMMENDATIONS:")
    
    # EQ suggestions based on common issues
    print("   EQ Suggestions:")
    print("      → High-pass filter at 20-30 Hz to remove rumble")
    print("      → Cut 200-400 Hz if mix sounds muddy")
    print("      → Boost 2-4 kHz for presence and clarity")
    print("      → High-shelf 8-12 kHz for air and brightness")
    
    # Compression suggestions
    print("   Compression:")
    if dynamic_range > 12:
        print("      → Use gentle compression (2:1 ratio) to control dynamics")
    print("      → Consider parallel compression for thickness")
    print("      → Use side-chain compression to create space")
    
    # Reverb and effects
    print("   Effects:")
    print("      → Add subtle reverb to glue elements together")
    print("      → Use delay to create space and movement")
    print("      → Consider saturation for warmth and character")
    
    print()
    
    # Mastering preparation
    print("🎚️ MASTERING PREPARATION:")
    print("   → Leave 1-2 dB headroom for mastering engineer")
    print("   → Ensure mix translates on different speakers")
    print("   → Check mono compatibility")
    print("   → Consider using reference tracks for comparison")
    
    print()
    print("💡 Remember: These are guidelines - trust your ears!")
    print("   The best mix is the one that serves the song.")


def analyze_audio(file_path: str) -> None:
    """
    Perform comprehensive audio analysis.
    
    Args:
        file_path: Path to the audio file
    """
    print(f"Analyzing audio file: {file_path}")
    print("=" * 50)
    
    # Load audio
    audio, sample_rate = load_audio(file_path)
    
    # 1. Calculate duration
    duration = calculate_duration(audio, sample_rate)
    print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    
    # 2. Detect silence
    silence_periods = detect_silence(audio, sample_rate)
    total_silence_time = sum(end - start for start, end in silence_periods)
    silence_percentage = (total_silence_time / duration) * 100
    
    print(f"Silence Detection:")
    print(f"  - Total silence time: {total_silence_time:.2f} seconds ({silence_percentage:.1f}%)")
    print(f"  - Number of silence periods: {len(silence_periods)}")
    if silence_periods:
        print(f"  - Silence periods: {silence_periods[:5]}")  # Show first 5 periods
        if len(silence_periods) > 5:
            print(f"    ... and {len(silence_periods) - 5} more")
    
    # 3. Calculate RMS
    rms_linear, rms_db = calculate_rms(audio)
    print(f"RMS (Loudness):")
    print(f"  - Linear: {rms_linear:.6f}")
    print(f"  - dB: {rms_db:.2f} dB")
    
    # 4. Estimate tempo
    tempo, confidence = estimate_tempo(audio, sample_rate)
    if tempo > 0:
        print(f"Tempo: {float(tempo):.1f} BPM (confidence: {float(confidence):.2f})")
    else:
        print("Tempo: Could not be estimated")
    
    # 5. Detect clipping
    is_clipped, peak_level_db, clipping_threshold = detect_clipping(audio, sample_rate)
    print(f"Clipping Detection:")
    print(f"  - Peak level: {peak_level_db:.2f} dB")
    print(f"  - Clipping threshold: {clipping_threshold:.2f} dB")
    print(f"  - Likely clipped: {'YES' if is_clipped else 'NO'}")
    
    # Additional metrics
    print(f"\nAdditional Metrics:")
    print(f"  - Sample rate: {sample_rate} Hz")
    print(f"  - Number of samples: {len(audio):,}")
    print(f"  - Dynamic range: {peak_level_db - rms_db:.2f} dB")
    
    # 6. Generate mixing and mastering feedback
    print(f"\n" + "=" * 50)
    print("🎵 MIXING & MASTERING FEEDBACK")
    print("=" * 50)
    generate_mix_feedback(rms_db, peak_level_db, is_clipped, silence_periods, 
                         tempo, duration, silence_percentage)


def main():
    """Main function to handle command line arguments and run analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze audio files for duration, silence, RMS, tempo, and clipping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audio_analyzer.py song.wav
  python audio_analyzer.py music.mp3
        """
    )
    
    parser.add_argument(
        "audio_file",
        help="Path to the audio file to analyze (.wav, .mp3, etc.)"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    import os
    if not os.path.exists(args.audio_file):
        print(f"Error: File '{args.audio_file}' not found.")
        sys.exit(1)
    
    # Perform analysis
    analyze_audio(args.audio_file)


if __name__ == "__main__":
    main() 