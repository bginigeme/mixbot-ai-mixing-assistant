# Mixbot - AI Mixing Assistant

A professional AI-powered mixing assistant that analyzes audio files and provides detailed mixing and mastering feedback. Available as both a command-line tool and a beautiful web application.

## 🎵 Features

- **Audio Analysis**: Comprehensive analysis of duration, silence, RMS, tempo, and clipping
- **Professional Mixing Feedback**: DAW-specific recommendations from a virtual mixing engineer
- **Web Interface**: Beautiful Streamlit UI for easy interaction
- **Command Line Tool**: Powerful CLI for batch processing and automation
- **Visualizations**: Interactive charts and meters for audio metrics
- **Downloadable Reports**: Export feedback as text files for reference

## Features

- **Duration Analysis**: Calculate the total duration of the audio track
- **Silence Detection**: Identify periods where the volume is below a threshold
- **RMS Calculation**: Compute the Root Mean Square (loudness) of the track
- **Tempo Estimation**: Estimate the tempo (BPM) using librosa's beat tracking
- **Clipping Detection**: Flag if any clipping is likely based on RMS or peak levels
- **Professional Mixing Feedback**: Get detailed mixing and mastering recommendations
- **Additional Metrics**: Sample rate, number of samples, and dynamic range

## 🚀 Quick Start

### Web Application (Recommended)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Launch the web app:**
```bash
python run_app.py
```

3. **Open your browser** and go to `http://localhost:8501`

4. **Upload your audio file**, select your DAW, and get instant feedback!

### Command Line Tool

For batch processing or automation:

```bash
python audio_analyzer.py <audio_file_path>
```

### Examples

```bash
# Web app (recommended)
python run_app.py

# Command line analysis
python audio_analyzer.py song.wav
python audio_analyzer.py music.mp3
python audio_analyzer.py audio.flac
```

## 🎛️ Web Application Features

### Upload & Analysis
- **Drag & Drop**: Easy file upload for WAV and MP3 files
- **DAW Selection**: Choose from 8 popular DAWs for specific recommendations
- **Vibe Input**: Add artist references or genre vibes for personalized feedback
- **Real-time Analysis**: Instant processing with progress indicators

### Visual Feedback
- **Interactive Charts**: Loudness meters and dynamic range gauges
- **Color-coded Metrics**: Green (good), Orange (warning), Red (critical)
- **Expandable Sections**: Organized feedback in collapsible sections
- **Quick Stats**: Key metrics displayed prominently

### Professional Feedback
- **Genre-Aware Analysis**: Automatic genre detection and tailored recommendations
- **Overall Assessment**: High-level track evaluation with genre context
- **Loudness Analysis**: Genre-specific RMS targets and recommendations
- **Clipping Detection**: Critical warnings and solutions
- **EQ Recommendations**: Genre-specific frequency suggestions with DAW plugins
- **Compression Tips**: Genre-appropriate dynamic range control with DAW plugins
- **Effects Guidance**: Reverb, delay, and saturation tips with DAW plugins
- **Third-Party Plugin Recommendations**: Professional plugin suggestions
- **Mastering Prep**: Export and quality check recommendations

### Export & Share
- **Download Reports**: Save feedback as timestamped text files
- **Session Persistence**: Results saved during browser session
- **Professional Formatting**: Clean, readable report structure

## Supported Formats

The script supports various audio formats including:
- WAV
- MP3
- FLAC
- OGG
- And other formats supported by librosa

## 📦 Dependencies

### Core Audio Analysis
- `librosa`: Professional audio analysis library
- `soundfile`: Audio file I/O and processing
- `numpy`: Numerical computing and array operations
- `scipy`: Scientific computing (required by librosa)

### Web Application
- `streamlit`: Modern web app framework
- `plotly`: Interactive data visualizations
- `pandas`: Data manipulation and analysis

## Example Output

```
🎵 MIXING & MASTERING FEEDBACK
==================================================
📊 ANALYSIS SUMMARY:
   • RMS Level: -13.7 dB
   • Peak Level: -0.3 dB
   • Dynamic Range: 13.4 dB
   • Tempo: 129 BPM
   • Silence: 6.6% of track

🔊 LOUDNESS & DYNAMICS:
   ✅ RMS level is in a good range for mastering
   ⚠️  Peak level is very close to clipping
      → Reduce peak levels by 1-2 dB
      → Check for transients that need taming

🎚️ CLIPPING & DISTORTION:
   ✅ No clipping detected - good headroom management

🎛️ SPECIFIC RECOMMENDATIONS:
   EQ Suggestions:
      → High-pass filter at 20-30 Hz to remove rumble
      → Cut 200-400 Hz if mix sounds muddy
      → Boost 2-4 kHz for presence and clarity
      → High-shelf 8-12 kHz for air and brightness
   Compression:
      → Use gentle compression (2:1 ratio) to control dynamics
      → Consider parallel compression for thickness
      → Use side-chain compression to create space
   Effects:
      → Add subtle reverb to glue elements together
      → Use delay to create space and movement
      → Consider saturation for warmth and character

🎚️ MASTERING PREPARATION:
   → Leave 1-2 dB headroom for mastering engineer
   → Ensure mix translates on different speakers
   → Check mono compatibility
   → Consider using reference tracks for comparison
```

## 📁 Project Structure

```
mixbot/
├── app.py                 # Streamlit web application
├── run_app.py            # App launcher script
├── audio_analyzer.py     # Core analysis engine
├── test_audio_analyzer.py # Test script
├── requirements.txt      # Python dependencies
├── README.md            # Documentation
└── venv/                # Virtual environment
```

## 🎯 Use Cases

- **Independent Artists**: Get professional mixing feedback without hiring an engineer
- **Music Producers**: Analyze tracks and get DAW-specific recommendations
- **Audio Engineers**: Use as a second opinion for mixing decisions
- **Students**: Learn mixing techniques through AI-guided feedback
- **Content Creators**: Ensure audio quality for videos and podcasts

## 🎛️ DAW-Specific Plugin Recommendations

Mixbot provides detailed plugin recommendations for 8 popular DAWs:

### Supported DAWs
- **FL Studio**: Fruity plugins, Maximus, built-in effects
- **Ableton Live**: EQ Eight, Glue Compressor, built-in effects
- **Logic Pro**: Channel EQ, Vintage compressors, Space Designer
- **Pro Tools**: Dyn3 series, Channel Strip, D-Verb
- **Cubase**: Frequency, StudioEQ, Roomworks
- **Reaper**: ReaEQ, ReaComp, ReaVerb
- **Studio One**: Pro EQ, Channel Strip, Room Reverb
- **Bitwig Studio**: EQ+, Multiband, built-in effects

### Plugin Categories
- **EQ Plugins**: Parametric, graphic, and surgical EQs
- **Compression Plugins**: Classic, multiband, and vintage compressors
- **Effects Plugins**: Reverb, delay, modulation, and saturation
- **Third-Party Recommendations**: Professional plugins from leading manufacturers

## 🎵 Genre-Aware Analysis

Mixbot automatically detects your track's genre and provides tailored recommendations:

### Supported Genres
- **Hip-Hop/Rap**: Heavy bass, punchy drums, clear vocals, wide stereo
- **Electronic/Dance**: Punchy kick, wide stereo, bright highs, tight compression
- **Rock**: Guitar presence, punchy drums, vocal clarity, natural dynamics
- **Pop**: Vocal forward, bright mix, wide stereo, consistent levels
- **Acoustic/Folk**: Natural dynamics, warm tones, minimal processing, space

### Genre-Specific Features
- **Loudness Targets**: Different RMS targets for each genre (Hip-Hop: -10dB, Electronic: -8dB, etc.)
- **EQ Focus**: Genre-appropriate frequency recommendations
- **Compression Styles**: Genre-specific compression techniques and settings
- **Characteristic Detection**: Automatic identification of genre characteristics

## 📝 Notes

- **Silence Detection**: Uses -40 dB threshold with 0.1s minimum duration
- **Tempo Estimation**: Works best with rhythmic music and clear beats
- **Clipping Detection**: Checks both peak levels and flat peak patterns
- **Format Support**: Automatically handles different sample rates and audio formats
- **Feedback Quality**: Based on industry standards and professional mixing practices
- **DAW Support**: Tailored recommendations for 8 popular DAWs 