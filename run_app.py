#!/usr/bin/env python3
"""
Mixbot Streamlit App Launcher

This script launches the Mixbot AI Mixing Assistant web application.
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit app"""
    print("🎵 Starting Mixbot - AI Mixing Assistant...")
    print("=" * 50)
    
    # Check if we're in the virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: It's recommended to run this in a virtual environment.")
        print("   Run: source venv/bin/activate")
        print()
    
    # Check if required files exist
    if not os.path.exists("app.py"):
        print("❌ Error: app.py not found!")
        print("   Make sure you're in the correct directory.")
        return
    
    if not os.path.exists("audio_analyzer.py"):
        print("❌ Error: audio_analyzer.py not found!")
        print("   Make sure the audio analyzer script is in the same directory.")
        return
    
    print("✅ All files found!")
    print("🚀 Launching Streamlit app...")
    print()
    print("📱 The app will open in your browser automatically.")
    print("🔗 If it doesn't, go to: http://localhost:8501")
    print()
    print("💡 Tips:")
    print("   - Upload WAV or MP3 files for analysis")
    print("   - Select your DAW for specific recommendations")
    print("   - Add vibe/artist references for personalized feedback")
    print("   - Download your feedback report as a text file")
    print()
    print("🛑 Press Ctrl+C to stop the app")
    print("=" * 50)
    
    try:
        # Launch Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Mixbot stopped. Thanks for using the AI Mixing Assistant!")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        print("   Make sure Streamlit is installed: pip install streamlit")

if __name__ == "__main__":
    main() 