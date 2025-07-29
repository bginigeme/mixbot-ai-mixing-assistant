#!/usr/bin/env python3
"""
Test script for audio_analyzer.py

This script demonstrates how to use the audio analyzer functions programmatically.
"""

import numpy as np
from audio_analyzer import (
    calculate_duration,
    detect_silence,
    calculate_rms,
    estimate_tempo,
    detect_clipping
)


def create_test_audio(duration=5.0, sample_rate=22050):
    """
    Create a test audio signal for demonstration.
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    # Create time array
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create a simple sine wave with some silence
    frequency = 440  # A4 note
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # Add some silence at the beginning and end
    silence_samples = int(0.5 * sample_rate)  # 0.5 seconds of silence
    audio[:silence_samples] = 0
    audio[-silence_samples:] = 0
    
    # Add some noise to make it more realistic
    noise = 0.01 * np.random.randn(len(audio))
    audio += noise
    
    return audio, sample_rate


def test_audio_analysis():
    """Test the audio analysis functions with a generated audio signal."""
    print("Testing Audio Analysis Functions")
    print("=" * 40)
    
    # Create test audio
    audio, sample_rate = create_test_audio(duration=5.0, sample_rate=22050)
    print(f"Generated test audio: {len(audio)} samples at {sample_rate} Hz")
    
    # Test duration calculation
    duration = calculate_duration(audio, sample_rate)
    print(f"\n1. Duration: {duration:.2f} seconds")
    
    # Test silence detection
    silence_periods = detect_silence(audio, sample_rate, threshold_db=-30.0)
    total_silence = sum(end - start for start, end in silence_periods)
    print(f"\n2. Silence Detection:")
    print(f"   - Found {len(silence_periods)} silence periods")
    print(f"   - Total silence time: {total_silence:.2f} seconds")
    print(f"   - Silence periods: {silence_periods}")
    
    # Test RMS calculation
    rms_linear, rms_db = calculate_rms(audio)
    print(f"\n3. RMS (Loudness):")
    print(f"   - Linear: {rms_linear:.6f}")
    print(f"   - dB: {rms_db:.2f} dB")
    
    # Test tempo estimation (will be low confidence for sine wave)
    tempo, confidence = estimate_tempo(audio, sample_rate)
    print(f"\n4. Tempo: {float(tempo):.1f} BPM (confidence: {float(confidence):.2f})")
    
    # Test clipping detection
    is_clipped, peak_level_db, clipping_threshold = detect_clipping(audio, sample_rate)
    print(f"\n5. Clipping Detection:")
    print(f"   - Peak level: {peak_level_db:.2f} dB")
    print(f"   - Clipping threshold: {clipping_threshold:.2f} dB")
    print(f"   - Likely clipped: {'YES' if is_clipped else 'NO'}")
    
    # Test with clipped audio
    print(f"\n" + "=" * 40)
    print("Testing with artificially clipped audio:")
    
    # Create clipped audio
    clipped_audio = audio.copy()
    clipped_audio[clipped_audio > 0.9] = 0.9  # Clip at 0.9
    clipped_audio[clipped_audio < -0.9] = -0.9
    
    is_clipped_clipped, peak_level_db_clipped, _ = detect_clipping(clipped_audio, sample_rate)
    print(f"   - Peak level: {peak_level_db_clipped:.2f} dB")
    print(f"   - Likely clipped: {'YES' if is_clipped_clipped else 'NO'}")


if __name__ == "__main__":
    test_audio_analysis() 