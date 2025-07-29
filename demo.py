#!/usr/bin/env python3
"""
Mixbot Demo Script

This script demonstrates how to use the Mixbot AI Mixing Assistant
programmatically without the web interface.
"""

import tempfile
import os
from audio_analyzer import analyze_audio, generate_mix_feedback
import numpy as np
import soundfile as sf

def create_demo_audio():
    """Create a demo audio file for testing"""
    # Parameters
    sample_rate = 44100
    duration = 5.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create a more complex signal
    # Main tone (440 Hz - A4)
    main_tone = 0.4 * np.sin(2 * np.pi * 440 * t)
    
    # Add harmonics
    harmonic1 = 0.2 * np.sin(2 * np.pi * 880 * t)  # 2nd harmonic
    harmonic2 = 0.1 * np.sin(2 * np.pi * 1320 * t)  # 3rd harmonic
    
    # Add some rhythm (simulate beats)
    beat_freq = 2.0  # 2 Hz = 120 BPM
    rhythm = 0.15 * np.sin(2 * np.pi * beat_freq * t)
    
    # Combine all components
    audio = main_tone + harmonic1 + harmonic2 + rhythm
    
    # Add some silence at the beginning and end
    silence_samples = int(0.3 * sample_rate)  # 0.3 seconds
    audio[:silence_samples] = 0
    audio[-silence_samples:] = 0
    
    # Add some noise
    noise = 0.02 * np.random.randn(len(audio))
    audio += noise
    
    # Normalize to prevent clipping
    audio = audio / np.max(np.abs(audio)) * 0.9
    
    return audio, sample_rate

def demo_analysis():
    """Demonstrate the analysis functionality"""
    print("🎵 Mixbot AI Mixing Assistant - Demo")
    print("=" * 50)
    
    # Create demo audio
    print("📝 Creating demo audio file...")
    audio, sample_rate = create_demo_audio()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        sf.write(tmp_file.name, audio, sample_rate)
        temp_path = tmp_file.name
    
    print(f"✅ Created demo audio: {len(audio)} samples at {sample_rate} Hz")
    print()
    
    # Run analysis
    print("🔍 Running audio analysis...")
    print("-" * 30)
    
    # Capture the output
    import sys
    from io import StringIO
    
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        analyze_audio(temp_path)
        analysis_output = captured_output.getvalue()
    finally:
        sys.stdout = old_stdout
        os.unlink(temp_path)
    
    print(analysis_output)
    
    # Extract metrics for feedback
    print("🎛️ Generating mixing feedback...")
    print("-" * 30)
    
    # Parse the output to extract metrics
    metrics = {}
    
    # Extract RMS
    if "dB:" in analysis_output:
        rms_lines = [line for line in analysis_output.split('\n') if "dB:" in line and "RMS" in line]
        if rms_lines:
            rms_db = rms_lines[0].split("dB:")[1].strip()
            metrics['rms_db'] = float(rms_db.split()[0])
    
    # Extract peak level
    if "Peak level:" in analysis_output:
        peak_line = [line for line in analysis_output.split('\n') if "Peak level:" in line][0]
        peak_db = peak_line.split("Peak level:")[1].strip()
        metrics['peak_db'] = float(peak_db.split()[0])
    
    # Extract tempo
    if "BPM" in analysis_output:
        tempo_lines = [line for line in analysis_output.split('\n') if "BPM" in line and "Tempo:" in line]
        if tempo_lines:
            tempo_str = tempo_lines[0].split("Tempo:")[1].split("BPM")[0].strip()
            metrics['tempo'] = float(tempo_str)
    
    # Extract silence percentage
    if "Silence:" in analysis_output:
        silence_lines = [line for line in analysis_output.split('\n') if "Silence:" in line and "%" in line]
        if silence_lines:
            silence_str = silence_lines[0].split("Silence:")[1].split("%")[0].strip()
            metrics['silence_percentage'] = float(silence_str)
    
    # Extract clipping status
    if "Likely clipped:" in analysis_output:
        clip_line = [line for line in analysis_output.split('\n') if "Likely clipped:" in line][0]
        clip_status = clip_line.split("Likely clipped:")[1].strip()
        metrics['clipping'] = "YES" in clip_status
    
    # Generate feedback for different DAWs
    daws = ["FL Studio", "Ableton Live", "Logic Pro"]
    vibe = "Demo track - Electronic vibes"
    
    # Prepare parameters for generate_mix_feedback
    rms_db = metrics.get('rms_db', -20)
    peak_level_db = metrics.get('peak_db', -10)
    is_clipped = metrics.get('clipping', False)
    silence_periods = []  # Demo doesn't have silence periods
    tempo = metrics.get('tempo', 120)
    duration = 5.0  # Demo duration
    silence_percentage = metrics.get('silence_percentage', 0)
    
    for daw in daws:
        print(f"\n🎛️ Feedback for {daw}:")
        print("-" * 40)
        
        # Use the generate_gpt_feedback function from the app
        from app import generate_gpt_feedback
        
        feedback_sections = generate_gpt_feedback(metrics, daw, vibe)
        
        # Show key sections
        if feedback_sections and 'overall' in feedback_sections:
            print(feedback_sections['overall'])
        if feedback_sections and 'loudness' in feedback_sections:
            print(feedback_sections['loudness'])
        if feedback_sections and 'clipping' in feedback_sections:
            print(feedback_sections['clipping'])
        
        # Show one specific recommendation
        if feedback_sections and 'compression' in feedback_sections:
            print(feedback_sections['compression'])
    
    print("\n" + "=" * 50)
    print("🎉 Demo complete!")
    print("\n💡 To use the full web interface:")
    print("   python run_app.py")
    print("\n💡 To analyze your own files:")
    print("   python audio_analyzer.py your_file.wav")

if __name__ == "__main__":
    demo_analysis() 