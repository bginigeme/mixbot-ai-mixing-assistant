import streamlit as st
import os
import tempfile
import io
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from audio_analyzer import analyze_audio, generate_mix_feedback
import numpy as np
import librosa
import soundfile as sf
import time
import json

# Analytics functions
def track_user_action(action, details=None):
    """Track user actions for analytics"""
    try:
        analytics_data = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "session_id": st.session_state.get("session_id", "unknown"),
            "page": "mixbot_main"
        }
        
        # Log to file (for simple tracking)
        with open("user_analytics.jsonl", "a") as f:
            f.write(json.dumps(analytics_data) + "\n")
        
        return analytics_data
    except Exception as e:
        # Silently fail if analytics fails
        pass

def initialize_analytics():
    """Initialize analytics for the session"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    # Track page view
    track_user_action("page_view")

def track_file_upload(file_name, file_size):
    """Track when users upload files"""
    track_user_action("file_upload", {
        "file_name": file_name,
        "file_size": file_size,
        "file_type": file_name.split(".")[-1] if "." in file_name else "unknown"
    })

def track_daw_selection(daw):
    """Track DAW selections"""
    track_user_action("daw_selection", {"daw": daw})

def track_genre_detection(genre):
    """Track detected genres"""
    track_user_action("genre_detection", {"genre": genre})

def track_feedback_download():
    """Track when users download feedback"""
    track_user_action("feedback_download")

def track_analysis_completion(analysis_time, file_size):
    """Track analysis completion"""
    track_user_action("analysis_complete", {
        "analysis_time_seconds": analysis_time,
        "file_size_mb": file_size
    })

def track_error(error_type, error_message, error_details=None, user_context=None):
    """Track errors for debugging and improvement"""
    try:
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "action": "error",
            "error_type": error_type,
            "error_message": str(error_message),
            "error_details": error_details,
            "user_context": user_context,
            "session_id": st.session_state.get("session_id", "unknown"),
            "page": "mixbot_main",
            "user_agent": st.session_state.get("user_agent", "unknown"),
            "file_uploaded": st.session_state.get("file_uploaded", False),
            "daw_selected": st.session_state.get("daw_selected", "none")
        }
        
        # Log to error file
        with open("error_log.jsonl", "a") as f:
            f.write(json.dumps(error_data) + "\n")
        
        # Also log to main analytics
        track_user_action("error", error_data)
        
        return error_data
    except Exception as e:
        # Fallback error logging
        try:
            with open("error_log_fallback.txt", "a") as f:
                f.write(f"{datetime.now().isoformat()}: {error_type} - {error_message}\n")
        except:
            pass  # Last resort - don't break the app

def track_file_processing_error(file_name, file_size, error_type, error_message):
    """Track file processing specific errors"""
    track_error(
        error_type=error_type,
        error_message=error_message,
        error_details={
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_name.split(".")[-1] if "." in file_name else "unknown"
        },
        user_context="file_processing"
    )

def track_analysis_error(analysis_step, error_type, error_message, metrics=None):
    """Track analysis specific errors"""
    track_error(
        error_type=error_type,
        error_message=error_message,
        error_details={
            "analysis_step": analysis_step,
            "metrics_available": list(metrics.keys()) if metrics else []
        },
        user_context="audio_analysis"
    )

def track_ui_error(ui_component, error_type, error_message):
    """Track UI specific errors"""
    track_error(
        error_type=error_type,
        error_message=error_message,
        error_details={"ui_component": ui_component},
        user_context="user_interface"
    )

def track_network_error(error_type, error_message, url=None, status_code=None, response_time=None):
    """Track network-related errors"""
    track_error(
        error_type=error_type,
        error_message=error_message,
        error_details={
            "url": url,
            "status_code": status_code,
            "response_time": response_time,
            "error_category": "network"
        },
        user_context="network_request"
    )

def track_streamlit_error(error_type, error_message, component=None, session_state=None):
    """Track Streamlit-specific errors"""
    track_error(
        error_type=error_type,
        error_message=error_message,
        error_details={
            "component": component,
            "session_state_keys": list(session_state.keys()) if session_state else [],
            "error_category": "streamlit"
        },
        user_context="streamlit_framework"
    )

def track_browser_error(error_type, error_message, user_agent=None, browser_info=None):
    """Track browser/client-side errors"""
    track_error(
        error_type=error_type,
        error_message=error_message,
        error_details={
            "user_agent": user_agent,
            "browser_info": browser_info,
            "error_category": "browser"
        },
        user_context="browser_client"
    )

# Page configuration
st.set_page_config(
    page_title="Mixbot - AI Mixing Assistant",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: #4a4a4a;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .feedback-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9fa;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Mobile responsive improvements */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
            margin-bottom: 1rem !important;
        }
        
        .sub-header {
            font-size: 1.2rem !important;
        }
        
        .metric-card {
            padding: 1rem !important;
            margin: 0.25rem 0 !important;
        }
        
        .feedback-section {
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
        }
        
        .upload-area {
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
        }
        
        /* Hide sidebar on very small screens */
        @media (max-width: 480px) {
            .css-1d391kg {
                display: none !important;
            }
        }
    }
    
    /* Mobile-friendly button styles */
    .stButton > button {
        width: 100% !important;
        margin: 0.5rem 0 !important;
    }
    
    /* Mobile-friendly file uploader */
    .stFileUploader > div {
        width: 100% !important;
    }
    
    /* Responsive columns */
    @media (max-width: 768px) {
        .row-widget.stHorizontal {
            flex-direction: column !important;
        }
        
        .row-widget.stHorizontal > div {
            width: 100% !important;
            margin-bottom: 1rem !important;
        }
    }
    
    /* Mobile-friendly expandable sections */
    @media (max-width: 768px) {
        .streamlit-expanderHeader {
            font-size: 1rem !important;
            padding: 0.75rem !important;
        }
        
        .streamlit-expanderContent {
            padding: 0.75rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'feedback_generated' not in st.session_state:
    st.session_state.feedback_generated = False

def load_and_analyze_audio(uploaded_file):
    """Load uploaded audio file and run analysis"""
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Capture the output from analyze_audio
        import sys
        from io import StringIO
        
        # Redirect stdout to capture analysis output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Run analysis
            analyze_audio(tmp_file_path)
            analysis_output = captured_output.getvalue()
        except Exception as analysis_error:
            # Track analysis-specific errors
            track_analysis_error(
                analysis_step="audio_analysis",
                error_type="analysis_failed",
                error_message=str(analysis_error),
                metrics={}
            )
            raise analysis_error
        finally:
            sys.stdout = old_stdout
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except Exception as cleanup_error:
                track_error("file_cleanup_failed", str(cleanup_error))
        
        return analysis_output, tmp_file_path
        
    except Exception as e:
        # Track file processing errors
        track_file_processing_error(
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            error_type="file_processing_failed",
            error_message=str(e)
        )
        st.error(f"Error analyzing audio: {str(e)}")
        return None, None

def extract_metrics_from_output(analysis_output):
    """Extract key metrics from analysis output"""
    metrics = {}
    
    # Extract duration
    if "Duration:" in analysis_output:
        duration_line = [line for line in analysis_output.split('\n') if "Duration:" in line][0]
        duration_str = duration_line.split("Duration:")[1].strip()
        metrics['duration'] = duration_str
    
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
    
    return metrics

def get_daw_plugins(daw):
    """Get DAW-specific plugin recommendations"""
    
    plugins = {
        "FL Studio": {
            "eq": """
- **Fruity Parametric EQ 2**: Surgical EQ with spectrum analyzer
- **Fruity Filter**: High-pass/low-pass filtering
- **Maximus**: Multiband compression and limiting
- **Fruity Limiter**: Peak limiting and compression
- **Fruity Reverb 2**: Convolution reverb
- **Fruity Delay 3**: Stereo delay with sync
- **Fruity Distortion**: Saturation and distortion
- **Fruity Compressor**: Classic compression
- **Fruity Stereo Enhancer**: Stereo width
- **Fruity Chorus**: Modulation effects""",
            
            "third_party": """
- **FabFilter Pro-Q 3**: Professional parametric EQ
- **Waves SSL E-Channel**: Console-style EQ and compression
- **iZotope Ozone**: Mastering suite
- **Valhalla Room**: Algorithmic reverb
- **Soundtoys EchoBoy**: Vintage delay emulation
- **Waves CLA-76**: 1176-style compression
- **FabFilter Pro-C 2**: Professional compression
- **iZotope Neutron**: Mixing assistant
- **Waves H-Delay**: Stereo delay
- **Soundtoys Decapitator**: Saturation and distortion""",
            
            "compression": """
- **Fruity Compressor**: Classic compression with visual feedback
- **Maximus**: Multiband compression and limiting
- **Fruity Limiter**: Peak limiting and compression
- **Fruity Multiband Compressor**: Frequency-specific compression
- **Fruity Peak Controller**: Side-chain compression
- **Fruity Balance**: Volume automation
- **Fruity Formula Controller**: Custom compression curves""",
            
            "expansion": """
- **Fruity Compressor**: Use in expansion mode
- **Fruity Peak Controller**: Dynamic expansion
- **Fruity Formula Controller**: Custom expansion curves
- **Fruity Balance**: Volume automation for expansion""",
            
            "effects": """
- **Fruity Reverb 2**: Convolution reverb with presets
- **Fruity Delay 3**: Stereo delay with tempo sync
- **Fruity Chorus**: Modulation and chorus effects
- **Fruity Flangus**: Flanger and phaser effects
- **Fruity Distortion**: Saturation and distortion
- **Fruity Stereo Enhancer**: Stereo width and enhancement
- **Fruity Phaser**: Phase shifting effects
- **Fruity Delay Bank**: Multiple delay lines
- **Fruity Reeverb 2**: Algorithmic reverb
- **Fruity Convolver**: Convolution effects"""
        },
        
        "Ableton Live": {
            "eq": """
- **EQ Eight**: 8-band parametric EQ with spectrum
- **EQ Three**: Simple 3-band EQ for quick adjustments
- **Auto Filter**: Auto-wah and filter effects
- **Multiband Dynamics**: Multiband compression
- **Utility**: Stereo width and phase adjustment
- **Spectrum**: Real-time spectrum analyzer
- **Tuner**: Pitch detection and tuning
- **Frequency Shifter**: Frequency manipulation""",
            
            "compression": """
- **Compressor**: Classic compression with visual feedback
- **Glue Compressor**: SSL-style bus compression
- **Multiband Dynamics**: Frequency-specific compression
- **Limiter**: Peak limiting and clipping prevention
- **Gate**: Noise gate and expansion
- **Drum Buss**: Drum-specific compression and saturation
- **Dynamic Tube**: Tube saturation and compression""",
            
            "expansion": """
- **Gate**: Noise gate and expansion
- **Multiband Dynamics**: Expansion in specific frequency bands
- **Compressor**: Use in expansion mode
- **Dynamic Tube**: Tube expansion effects""",
            
            "effects": """
- **Reverb**: Algorithmic reverb with multiple algorithms
- **Delay**: Stereo delay with tempo sync
- **Echo**: Vintage delay emulation
- **Chorus**: Modulation and chorus effects
- **Flanger**: Flanging effects
- **Phaser**: Phase shifting effects
- **Auto Pan**: Automatic panning
- **Auto Filter**: Auto-wah and filter effects
- **Saturator**: Saturation and distortion
- **Overdrive**: Overdrive effects""",
            
            "third_party": """
- **FabFilter Pro-Q 3**: Professional parametric EQ
- **Waves SSL E-Channel**: Console-style EQ and compression
- **iZotope Ozone**: Mastering suite
- **Valhalla Room**: Algorithmic reverb
- **Soundtoys EchoBoy**: Vintage delay emulation
- **Waves CLA-76**: 1176-style compression
- **FabFilter Pro-C 2**: Professional compression
- **iZotope Neutron**: Mixing assistant
- **Waves H-Delay**: Stereo delay
- **Soundtoys Decapitator**: Saturation and distortion"""
        },
        
        "Logic Pro": {
            "eq": """
- **Channel EQ**: 8-band parametric EQ with spectrum
- **Linear Phase EQ**: Phase-corrected EQ
- **Match EQ**: Match frequency response of reference
- **Single Band EQ**: Simple single-band EQ
- **Fat EQ**: Vintage EQ emulation
- **Vintage Console EQ**: Console-style EQ
- **Vintage Graphic EQ**: Graphic EQ emulation
- **Spectrum Analyzer**: Real-time spectrum display""",
            
            "compression": """
- **Compressor**: Classic compression with multiple algorithms
- **Vintage FET Compressor**: 1176-style compression
- **Vintage VCA Compressor**: SSL-style compression
- **Vintage Opto Compressor**: LA-2A-style compression
- **Multipressor**: Multiband compression
- **Adaptive Limiter**: Peak limiting and clipping prevention
- **Enveloper**: Envelope-based compression
- **Dynamics Processor**: Advanced dynamics control""",
            
            "expansion": """
- **Noise Gate**: Noise gate and expansion
- **Enveloper**: Envelope-based expansion
- **Dynamics Processor**: Advanced expansion control
- **Compressor**: Use in expansion mode""",
            
            "effects": """
- **Space Designer**: Convolution reverb
- **ChromaVerb**: Algorithmic reverb
- **Stereo Delay**: Stereo delay with tempo sync
- **Tape Delay**: Vintage delay emulation
- **Chorus**: Modulation and chorus effects
- **Flanger**: Flanging effects
- **Phaser**: Phase shifting effects
- **Tremolo**: Tremolo effects
- **Distortion**: Distortion and saturation
- **Bitcrusher**: Bit reduction and sample rate effects"""
        },
        
        "Pro Tools": {
            "eq": """
- **EQ3**: 7-band parametric EQ
- **EQ7**: 7-band parametric EQ with spectrum
- **Channel Strip**: Console-style EQ and dynamics
- **DigiRack EQ**: Classic Pro Tools EQ
- **BF-2A**: Pultec-style EQ
- **BF-3A**: 3-band parametric EQ
- **BF-76**: 1176-style compressor with EQ
- **BF-2A**: LA-2A-style compressor with EQ""",
            
            "compression": """
- **Dyn3 Compressor**: Classic compression
- **Dyn3 Compressor/Limiter**: Compression and limiting
- **Dyn3 Expander/Gate**: Expansion and gating
- **Channel Strip**: Console-style compression
- **BF-76**: 1176-style compression
- **BF-2A**: LA-2A-style compression
- **BF-3A**: 3-band compression
- **Multiband Dynamics**: Frequency-specific compression""",
            
            "expansion": """
- **Dyn3 Expander/Gate**: Expansion and gating
- **Channel Strip**: Console-style expansion
- **BF-3A**: 3-band expansion
- **Multiband Dynamics**: Frequency-specific expansion""",
            
            "effects": """
- **D-Verb**: Algorithmic reverb
- **Space**: Convolution reverb
- **Mod Delay III**: Stereo delay with modulation
- **Long Delay III**: Long delay effects
- **Short Delay III**: Short delay effects
- **Flanger**: Flanging effects
- **Chorus**: Chorus effects
- **Phaser**: Phase shifting effects
- **Lo-Fi**: Bit reduction and sample rate effects
- **SansAmp**: Amp simulation and distortion"""
        },
        
        "Cubase": {
            "eq": """
- **Frequency**: 8-band parametric EQ
- **StudioEQ**: Professional parametric EQ
- **GEQ-30**: 30-band graphic EQ
- **VST Amp Rack**: Amp simulation with EQ
- **Multiband Compressor**: Multiband compression with EQ
- **Channel Strip**: Console-style EQ and dynamics
- **Spectrum Analyzer**: Real-time spectrum display""",
            
            "compression": """
- **Compressor**: Classic compression
- **Multiband Compressor**: Frequency-specific compression
- **Tube Compressor**: Tube compression emulation
- **Vintage Compressor**: Vintage compression emulation
- **Limiter**: Peak limiting
- **Gate**: Noise gate and expansion
- **Envelope Shaper**: Envelope-based compression""",
            
            "expansion": """
- **Gate**: Noise gate and expansion
- **Envelope Shaper**: Envelope-based expansion
- **Multiband Compressor**: Frequency-specific expansion
- **Compressor**: Use in expansion mode""",
            
            "effects": """
- **Reverb**: Algorithmic reverb
- **Roomworks**: Room simulation
- **REVerence**: Convolution reverb
- **Delay**: Stereo delay with tempo sync
- **ModMachine**: Modulation effects
- **Chorus**: Chorus effects
- **Flanger**: Flanging effects
- **Phaser**: Phase shifting effects
- **Distortion**: Distortion and saturation
- **Bitcrusher**: Bit reduction effects"""
        },
        
        "Reaper": {
            "eq": """
- **ReaEQ**: Parametric EQ with spectrum
- **ReaFir**: Linear phase EQ and spectrum analyzer
- **ReaXcomp**: Multiband compression with EQ
- **ReaComp**: Compression with side-chain EQ
- **JS: Graphic EQ**: Graphic EQ
- **JS: 3-Band EQ**: Simple 3-band EQ
- **JS: 5-Band EQ**: Simple 5-band EQ
- **JS: 7-Band EQ**: Simple 7-band EQ""",
            
            "compression": """
- **ReaComp**: Classic compression with side-chain
- **ReaXcomp**: Multiband compression
- **ReaGate**: Noise gate and expansion
- **ReaLimit**: Peak limiting
- **JS: Compressor**: Simple compression
- **JS: Limiter**: Simple limiting
- **JS: Gate**: Simple gating
- **JS: Multiband Compressor**: Multiband compression""",
            
            "expansion": """
- **ReaGate**: Noise gate and expansion
- **JS: Gate**: Simple gating and expansion
- **ReaComp**: Use in expansion mode
- **JS: Compressor**: Use in expansion mode""",
            
            "effects": """
- **ReaVerb**: Convolution reverb
- **ReaDelay**: Stereo delay with tempo sync
- **ReaChorus**: Chorus effects
- **ReaFlanger**: Flanging effects
- **ReaPhaser**: Phase shifting effects
- **ReaTune**: Pitch correction
- **ReaPitch**: Pitch shifting
- **JS: Reverb**: Simple reverb
- **JS: Delay**: Simple delay
- **JS: Chorus**: Simple chorus"""
        },
        
        "Studio One": {
            "eq": """
- **Pro EQ**: Professional parametric EQ
- **Splitter**: Multiband processing with EQ
- **Channel Strip**: Console-style EQ and dynamics
- **Mix Tool**: Simple EQ and dynamics
- **Tone Generator**: Test tone generator
- **Spectrum Meter**: Real-time spectrum display
- **VU Meter**: VU metering
- **Phase Meter**: Phase correlation meter""",
            
            "compression": """
- **Compressor**: Classic compression
- **Multiband Dynamics**: Multiband compression
- **Channel Strip**: Console-style compression
- **Mix Tool**: Simple compression
- **Limiter**: Peak limiting
- **Gate**: Noise gate and expansion
- **Envelope Shaper**: Envelope-based compression
- **Splitter**: Multiband processing""",
            
            "expansion": """
- **Gate**: Noise gate and expansion
- **Envelope Shaper**: Envelope-based expansion
- **Multiband Dynamics**: Frequency-specific expansion
- **Splitter**: Multiband processing for expansion""",
            
            "effects": """
- **Room Reverb**: Algorithmic reverb
- **Open Air**: Convolution reverb
- **Delay**: Stereo delay with tempo sync
- **Chorus**: Chorus effects
- **Flanger**: Flanging effects
- **Phaser**: Phase shifting effects
- **Tremolo**: Tremolo effects
- **Distortion**: Distortion and saturation
- **Bitcrusher**: Bit reduction effects
- **Mix Tool**: Simple effects processing"""
        },
        
        "Bitwig Studio": {
            "eq": """
- **EQ+**: Parametric EQ with spectrum
- **EQ-5**: 5-band parametric EQ
- **Multiband**: Multiband processing with EQ
- **Channel EQ**: Console-style EQ
- **Spectrum**: Real-time spectrum analyzer
- **Tuner**: Pitch detection and tuning
- **Frequency Shifter**: Frequency manipulation
- **Resonator**: Resonant filter effects""",
            
            "compression": """
- **Compressor**: Classic compression
- **Multiband**: Multiband compression
- **Limiter**: Peak limiting
- **Gate**: Noise gate and expansion
- **Transient**: Transient shaping
- **Channel**: Console-style compression
- **Dynamics**: Advanced dynamics control
- **Sidechain**: Side-chain compression""",
            
            "expansion": """
- **Gate**: Noise gate and expansion
- **Transient**: Transient expansion
- **Dynamics**: Advanced expansion control
- **Multiband**: Frequency-specific expansion""",
            
            "effects": """
- **Reverb**: Algorithmic reverb
- **Delay**: Stereo delay with tempo sync
- **Chorus**: Chorus effects
- **Flanger**: Flanging effects
- **Phaser**: Phase shifting effects
- **Tremolo**: Tremolo effects
- **Distortion**: Distortion and saturation
- **Bitcrusher**: Bit reduction effects
- **Resonator**: Resonant filter effects
- **Frequency Shifter**: Frequency manipulation"""
        }
    }
    
    return plugins.get(daw, {
        "eq": "- Use built-in EQ plugins for your DAW",
        "compression": "- Use built-in compression plugins for your DAW", 
        "expansion": "- Use built-in expansion plugins for your DAW",
        "effects": "- Use built-in effects plugins for your DAW",
        "third_party": "- Consider professional third-party plugins for your DAW"
    })


def analyze_genre_characteristics(tempo, vibe, metrics):
    """Analyze genre characteristics based on tempo, vibe, and metrics"""
    
    # Default genre analysis
    genre_info = {
        'genre': 'Unknown',
        'characteristics': [],
        'loudness_target': -14,
        'compression_style': 'moderate',
        'eq_focus': 'balanced'
    }
    
    # Analyze based on vibe keywords
    vibe_lower = vibe.lower() if vibe else ""
    
    if any(word in vibe_lower for word in ['hip', 'rap', 'trap', 'drill', 'jay', 'kendrick', 'drake']):
        genre_info.update({
            'genre': 'Hip-Hop/Rap',
            'characteristics': ['heavy bass', 'punchy drums', 'clear vocals', 'wide stereo'],
            'loudness_target': -10,
            'compression_style': 'aggressive',
            'eq_focus': 'bass and presence'
        })
    elif any(word in vibe_lower for word in ['edm', 'electronic', 'dance', 'house', 'techno', 'trance']):
        genre_info.update({
            'genre': 'Electronic/Dance',
            'characteristics': ['punchy kick', 'wide stereo', 'bright highs', 'tight compression'],
            'loudness_target': -8,
            'compression_style': 'tight',
            'eq_focus': 'kick and highs'
        })
    elif any(word in vibe_lower for word in ['rock', 'guitar', 'band', 'live']):
        genre_info.update({
            'genre': 'Rock',
            'characteristics': ['guitar presence', 'punchy drums', 'vocal clarity', 'natural dynamics'],
            'loudness_target': -12,
            'compression_style': 'moderate',
            'eq_focus': 'guitars and vocals'
        })
    elif any(word in vibe_lower for word in ['pop', 'mainstream', 'radio']):
        genre_info.update({
            'genre': 'Pop',
            'characteristics': ['vocal forward', 'bright mix', 'wide stereo', 'consistent levels'],
            'loudness_target': -10,
            'compression_style': 'consistent',
            'eq_focus': 'vocals and brightness'
        })
    elif any(word in vibe_lower for word in ['acoustic', 'folk', 'singer', 'guitar']):
        genre_info.update({
            'genre': 'Acoustic/Folk',
            'characteristics': ['natural dynamics', 'warm tones', 'minimal processing', 'space'],
            'loudness_target': -16,
            'compression_style': 'gentle',
            'eq_focus': 'warmth and clarity'
        })
    
    # Override with tempo-based analysis if no vibe detected
    if genre_info['genre'] == 'Unknown':
        if tempo > 140:
            genre_info.update({
                'genre': 'Fast Electronic/Dance',
                'characteristics': ['high energy', 'tight compression', 'bright mix'],
                'loudness_target': -8,
                'compression_style': 'tight',
                'eq_focus': 'kick and highs'
            })
        elif tempo > 120:
            genre_info.update({
                'genre': 'Pop/Rock',
                'characteristics': ['moderate energy', 'balanced mix', 'clear vocals'],
                'loudness_target': -12,
                'compression_style': 'moderate',
                'eq_focus': 'balanced'
            })
        elif tempo > 90:
            genre_info.update({
                'genre': 'Hip-Hop/Rap',
                'characteristics': ['punchy drums', 'heavy bass', 'clear vocals'],
                'loudness_target': -10,
                'compression_style': 'aggressive',
                'eq_focus': 'bass and presence'
            })
        else:
            genre_info.update({
                'genre': 'Slow/Ambient',
                'characteristics': ['atmospheric', 'gentle dynamics', 'warm tones'],
                'loudness_target': -16,
                'compression_style': 'gentle',
                'eq_focus': 'warmth and space'
            })
    
    return genre_info


def generate_gpt_feedback(metrics, daw, vibe=""):
    """Generate GPT-style feedback based on metrics and user inputs"""
    
    feedback_sections = {}
    
    # Analyze genre characteristics
    genre_info = analyze_genre_characteristics(metrics.get('tempo', 120), vibe, metrics)
    
    # Overall assessment with genre context
    rms_db = metrics.get('rms_db', -20)
    tempo = metrics.get('tempo', 120)
    
    # Genre-specific assessment
    if genre_info['genre'] == 'Hip-Hop/Rap':
        if rms_db < -15:
            energy_desc = "needs more punch for hip-hop"
            energy_emoji = "❌"
        elif rms_db < -10:
            energy_desc = "has good hip-hop energy"
            energy_emoji = "✅"
        else:
            energy_desc = "is well-mixed for hip-hop"
            energy_emoji = "🎵"
    elif genre_info['genre'] == 'Electronic/Dance':
        if rms_db < -12:
            energy_desc = "needs more energy for dance music"
            energy_emoji = "❌"
        elif rms_db < -8:
            energy_desc = "has good dance floor energy"
            energy_emoji = "✅"
        else:
            energy_desc = "is well-mixed for electronic music"
            energy_emoji = "🎵"
    else:
        if rms_db < -16:
            energy_desc = "needs more energy"
            energy_emoji = "❌"
        elif rms_db < -12:
            energy_desc = "has good energy"
            energy_emoji = "✅"
        else:
            energy_desc = "is well-mixed"
            energy_emoji = "🎵"
    
    feedback_sections['overall'] = f"""
🎵 **Overall Assessment - {genre_info['genre']}**
{energy_emoji} Your track {energy_desc} with a {'good' if not metrics.get('clipping', False) else 'concerning'} dynamic range. 
The {tempo:.0f} BPM tempo {'works well' if 80 <= tempo <= 160 else 'may need attention'} for {genre_info['genre'].lower()}.

**Genre Characteristics Detected:**
{chr(10).join([f"• {char}" for char in genre_info['characteristics']])}
"""
    
    # Genre-aware loudness analysis
    rms_db = metrics.get('rms_db', 0)
    target_rms = genre_info['loudness_target']
    
    if rms_db > target_rms + 3:
        feedback_sections['loudness'] = f"""
🔊 **Loudness Issues - Too Hot for {genre_info['genre']}**
Your track is too loud for {genre_info['genre'].lower()} mastering. Target RMS should be around {target_rms} dB.
**In {daw}:**
- Lower your master fader by 3-5 dB
- Check individual track levels - they're likely too hot
- Use a limiter with -1 dB ceiling before the master
- Consider using a VU meter plugin to monitor levels
"""
    elif rms_db < target_rms - 3:
        feedback_sections['loudness'] = f"""
🔊 **Loudness - Too Quiet for {genre_info['genre']}**
Your track has good headroom but is too quiet for {genre_info['genre'].lower()}. Target RMS should be around {target_rms} dB.
**In {daw}:**
- Consider {genre_info['compression_style']} compression to bring up quiet parts
- Use parallel compression for thickness
- Ensure your mix translates well on different systems
- You can safely increase overall level by 2-3 dB
"""
    else:
        feedback_sections['loudness'] = f"""
🔊 **Loudness - Perfect for {genre_info['genre']}**
Your RMS level is in the sweet spot for {genre_info['genre'].lower()} mastering.
**In {daw}:**
- Keep your current levels
- Consider subtle compression for consistency
- You're ready for the mastering stage
"""
    
    # Clipping analysis
    if metrics.get('clipping', False):
        feedback_sections['clipping'] = """
❌ **CRITICAL: Clipping Detected**
This will destroy your mix quality and cause distortion.
**In {daw}:**
- Immediately reduce master fader by 5-8 dB
- Check every track for red meters
- Use a limiter with -1 dB ceiling
- Consider using soft clipping for character instead
- Re-export your mix with proper headroom
"""
    else:
        feedback_sections['clipping'] = """
✅ **No Clipping - Good Headroom Management**
Your track has proper headroom for mastering.
**In {daw}:**
- Maintain your current peak levels
- You can safely add effects without worry
- Consider using a limiter for consistency
"""
    
    # Genre-aware EQ recommendations with plugin suggestions
    daw_plugins = get_daw_plugins(daw)
    
    # Genre-specific EQ advice
    if genre_info['genre'] == 'Hip-Hop/Rap':
        eq_advice = f"""
**Hip-Hop/Rap EQ Focus:**
- **Bass (60-120 Hz)**: Boost for heavy, punchy bass
- **Kick (80-100 Hz)**: Cut competing frequencies in other tracks
- **Vocals (2-4 kHz)**: Boost for clarity and presence
- **Highs (8-12 kHz)**: High-shelf for brightness and air
- **Low-Mid Cuts**: Cut 200-400 Hz in non-essential tracks to reduce mud
"""
    elif genre_info['genre'] == 'Electronic/Dance':
        eq_advice = f"""
**Electronic/Dance EQ Focus:**
- **Kick (60-80 Hz)**: Boost for punch and dance floor impact
- **Bass (100-200 Hz)**: Tight, controlled bass
- **Highs (10-15 kHz)**: Bright, energetic highs
- **Mid Cuts**: Cut 400-800 Hz to reduce boxiness
- **Stereo Width**: Enhance 8-12 kHz for wide, open sound
"""
    elif genre_info['genre'] == 'Rock':
        eq_advice = f"""
**Rock EQ Focus:**
- **Guitars (2-4 kHz)**: Boost for presence and cut-through
- **Drums (80-120 Hz)**: Punchy, natural drum sound
- **Vocals (3-5 kHz)**: Clear, forward vocals
- **Bass (100-200 Hz)**: Warm, supporting bass
- **Highs (8-12 kHz)**: Natural brightness without harshness
"""
    elif genre_info['genre'] == 'Pop':
        eq_advice = f"""
**Pop EQ Focus:**
- **Vocals (2-5 kHz)**: Forward, clear vocals
- **Bass (80-150 Hz)**: Tight, controlled bass
- **Highs (10-15 kHz)**: Bright, radio-friendly highs
- **Mid Cuts**: Cut 300-600 Hz to reduce mud
- **Stereo Width**: Wide, open mix
"""
    else:
        eq_advice = f"""
**General EQ Focus:**
- **High-Pass Filter**: Apply at 20-30 Hz to remove rumble
- **Low-Mid Cuts**: Cut 200-400 Hz if mix sounds muddy
- **Presence Boost**: Boost 2-4 kHz for clarity and definition
- **Air Frequencies**: High-shelf 8-12 kHz for brightness
"""
    
    feedback_sections['eq'] = f"""
🎛️ **EQ Recommendations for {daw} - {genre_info['genre']}**
Based on your track's characteristics:

{eq_advice}

**{daw}-Specific EQ Plugins:**
{daw_plugins['eq']}

**General EQ Tips:**
- Use the built-in EQ with surgical precision
- Consider using a spectrum analyzer
- A/B with reference tracks
- Focus on {genre_info['eq_focus']} for {genre_info['genre'].lower()}
"""
    
    # Genre-aware compression recommendations with plugin suggestions
    dynamic_range = metrics.get('peak_db', 0) - metrics.get('rms_db', 0)
    daw_plugins = get_daw_plugins(daw)
    
    # Genre-specific compression advice
    if genre_info['genre'] == 'Hip-Hop/Rap':
        comp_advice = f"""
**Hip-Hop/Rap Compression:**
- **Aggressive compression** on drums for punch
- **Side-chain compression** on bass from kick
- **Parallel compression** on vocals for thickness
- **Multiband compression** on master for control
- **Attack: 5-15ms, Release: 50-150ms** for punchy sound
"""
    elif genre_info['genre'] == 'Electronic/Dance':
        comp_advice = f"""
**Electronic/Dance Compression:**
- **Tight compression** on kick and bass
- **Side-chain compression** for pumping effect
- **Parallel compression** on drums for impact
- **Multiband compression** for frequency control
- **Attack: 1-10ms, Release: 30-100ms** for tight sound
"""
    elif genre_info['genre'] == 'Rock':
        comp_advice = f"""
**Rock Compression:**
- **Moderate compression** on guitars and vocals
- **Natural compression** on drums
- **Parallel compression** for thickness
- **Bus compression** for glue
- **Attack: 10-30ms, Release: 100-300ms** for natural sound
"""
    elif genre_info['genre'] == 'Pop':
        comp_advice = f"""
**Pop Compression:**
- **Consistent compression** on vocals
- **Tight compression** on drums
- **Parallel compression** for thickness
- **Bus compression** for consistency
- **Attack: 5-20ms, Release: 50-200ms** for consistent sound
"""
    else:
        comp_advice = f"""
**General Compression:**
- **Gentle compression** on individual tracks
- **Parallel compression** for thickness
- **Side-chain compression** to create space
- **Multiband compression** for complex material
- **Attack: 10-30ms, Release: 100-300ms**
"""
    
    if dynamic_range > 15:
        feedback_sections['compression'] = f"""
🎚️ **Compression Needed - High Dynamic Range for {genre_info['genre']}**
Your track has large dynamics that need control.

**In {daw}:**
{comp_advice}

**{daw}-Specific Compression Plugins:**
{daw_plugins['compression']}
"""
    elif dynamic_range < 6:
        feedback_sections['compression'] = f"""
🎚️ **Over-Compression Warning for {genre_info['genre']}**
Your track is very compressed/limited.

**In {daw}:**
- Back off on compression/limiting
- Allow more natural dynamics
- Consider using expansion for breathing room
- Check if you're over-processing

**{daw}-Specific Expansion Plugins:**
{daw_plugins['expansion']}
"""
    else:
        feedback_sections['compression'] = f"""
🎚️ **Compression - Good Balance for {genre_info['genre']}**
Your dynamics are well-controlled.

**In {daw}:**
{comp_advice}

**{daw}-Specific Compression Plugins:**
{daw_plugins['compression']}
"""
    
    # Effects recommendations with plugin suggestions
    feedback_sections['effects'] = f"""
✨ **Effects Recommendations for {daw}**

**Reverb:**
- Add subtle reverb to glue elements together
- Use different reverb types for different elements
- Keep reverb levels low to avoid muddiness

**Delay:**
- Use delay to create space and movement
- Sync delays to your {metrics.get('tempo', 120):.0f} BPM tempo
- Consider ping-pong delays for width

**Saturation:**
- Add warmth and character with saturation
- Use on individual tracks, not the master
- Consider tape saturation for vintage feel

**{daw}-Specific Effects Plugins:**
{daw_plugins['effects']}

**General Effects Tips:**
- Use built-in effects for consistency
- Consider third-party plugins for character
- A/B with bypass to ensure improvements
"""
    
    # Vibe-specific recommendations
    if vibe:
        feedback_sections['vibe'] = f"""
🎭 **Vibe-Specific Recommendations**
Based on your "{vibe}" reference:

**Mood Matching:**
- Study the reference track's frequency balance
- Match the overall energy and dynamics
- Pay attention to space and arrangement

**Genre Considerations:**
- Apply genre-appropriate processing
- Use reference tracks for comparison
- Consider genre-specific mixing techniques

**{daw} Workflow:**
- Use reference tracks in your DAW
- A/B your mix with the reference
- Match levels and frequency balance
"""
    
    # Mastering preparation
    feedback_sections['mastering'] = f"""
🎚️ **Mastering Preparation for {daw}**

**Export Settings:**
- Leave 1-2 dB headroom for mastering engineer
- Export at 24-bit, 44.1kHz or higher
- Use WAV format for best quality

**Quality Checks:**
- Ensure mix translates on different speakers
- Check mono compatibility
- Test on headphones and car speakers

**Reference Tracks:**
- Use professional reference tracks
- Match levels and frequency balance
- Consider using a reference track plugin

**{daw} Export Tips:**
- Use the highest quality export settings
- Consider using a mastering limiter
- Check for any remaining clipping

**Recommended Third-Party Plugins:**
{daw_plugins['third_party']}
"""
    
    return feedback_sections

def create_visualizations(metrics):
    """Create visualizations for the metrics"""
    
    # Loudness meter
    fig_loudness = go.Figure()
    
    rms_db = metrics.get('rms_db', -20)
    peak_db = metrics.get('peak_db', -10)
    
    # Color coding based on levels
    rms_color = 'red' if rms_db > -8 else 'orange' if rms_db > -12 else 'green'
    peak_color = 'red' if peak_db > -1 else 'orange' if peak_db > -3 else 'green'
    
    fig_loudness.add_trace(go.Bar(
        x=['RMS', 'Peak'],
        y=[rms_db, peak_db],
        marker_color=[rms_color, peak_color],
        text=[f'{rms_db:.1f} dB', f'{peak_db:.1f} dB'],
        textposition='auto',
    ))
    
    fig_loudness.update_layout(
        title="Loudness Analysis",
        yaxis_title="Level (dB)",
        yaxis=dict(range=[-30, 0]),
        height=300
    )
    
    # Dynamic range visualization
    dynamic_range = peak_db - rms_db
    fig_dynamic = go.Figure()
    
    fig_dynamic.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=dynamic_range,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Dynamic Range (dB)"},
        delta={'reference': 12},
        gauge={
            'axis': {'range': [None, 20]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 6], 'color': "lightgray"},
                {'range': [6, 12], 'color': "yellow"},
                {'range': [12, 20], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 15
            }
        }
    ))
    
    fig_dynamic.update_layout(height=300)
    
    return fig_loudness, fig_dynamic

def main():
    # Initialize analytics
    initialize_analytics()
    
    # Global error handling wrapper
    try:
        main_app_content()
    except Exception as e:
        # Track any unhandled errors
        track_error(
            error_type="unhandled_exception",
            error_message=str(e),
            error_details={
                "exception_type": type(e).__name__,
                "traceback": str(e),
                "error_category": "unhandled"
            },
            user_context="main_app"
        )
        st.error(f"❌ An unexpected error occurred: {str(e)}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

def main_app_content():
    
    # Header
    st.markdown('<h1 class="main-header">🎵 Mixbot</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered Mixing Assistant</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Settings")
        st.markdown("*Configure your analysis preferences*")
        
        # DAW selection
        try:
            daw_options = [
                "FL Studio", "Ableton Live", "Logic Pro", "Pro Tools", 
                "Cubase", "Reaper", "Studio One", "Bitwig Studio"
            ]
            selected_daw = st.selectbox("Select your DAW:", daw_options, 
                                       help="Choose your DAW for specific plugin recommendations")
            
            # Track DAW selection
            if selected_daw:
                track_daw_selection(selected_daw)
                st.session_state.daw_selected = selected_daw
        except Exception as e:
            track_streamlit_error(
                error_type="daw_selection_error",
                error_message=str(e),
                component="selectbox",
                session_state=st.session_state
            )
            st.error("Error with DAW selection component")
            selected_daw = "FL Studio"  # Default fallback
        
        # Vibe/Reference input
        vibe_reference = st.text_input("Vibe/Artist Reference (optional):", 
                                     placeholder="e.g., 'The Weeknd vibes' or 'Dark trap'",
                                     help="Add genre or artist reference for personalized feedback")
        
        st.markdown("---")
        st.markdown("### 📊 About")
        st.markdown("""
        **Mixbot** analyzes your audio and provides professional mixing feedback tailored to your DAW.
        
        **Features:**
        - 🎵 Audio analysis
        - 🎛️ DAW-specific recommendations  
        - 🎚️ Professional mixing tips
        - 🎧 Mastering preparation
        """)
        
        st.markdown("---")
        st.markdown("### 📱 Mobile Tips")
        st.markdown("""
        - **Tap ☰** to open/close settings
        - **Swipe** to navigate sections
        - **Pinch** to zoom charts
        """)
        
        st.markdown("---")
        st.markdown("### 🐛 Report Issues")
        if st.button("🚨 Report a Bug"):
            st.info("""
            **If you encounter any errors (like AxiosError):**
            1. Check your browser console (F12)
            2. Try refreshing the page
            3. Use a different browser
            4. Contact support with error details
            """)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Mobile-friendly settings toggle
        st.markdown("""
        <div style="text-align: right; margin-bottom: 1rem;">
            <small>💡 <strong>Tip:</strong> Use the sidebar (☰) for DAW settings and vibe input</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Network status indicator
        try:
            import requests
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            if response.status_code == 200:
                st.markdown("""
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 0.5rem; margin-bottom: 1rem;">
                    <small>🌐 <strong>Network Status:</strong> Connected</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 0.5rem; margin-bottom: 1rem;">
                    <small>⚠️ <strong>Network Status:</strong> Slow connection detected</small>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown("""
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 0.5rem; margin-bottom: 1rem;">
                <small>❌ <strong>Network Status:</strong> Connection issues detected</small>
            </div>
            """, unsafe_allow_html=True)
            # Track network connectivity issues
            track_network_error(
                error_type="connectivity_test_failed",
                error_message=str(e),
                url="https://httpbin.org/status/200"
            )
        
        st.markdown('<h2 class="sub-header">📁 Upload Your Track</h2>', unsafe_allow_html=True)
        
        # File upload
        try:
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=['wav', 'mp3'],
                help="Upload a WAV or MP3 file for analysis"
            )
            
            if uploaded_file is not None:
                # Track file upload
                track_file_upload(uploaded_file.name, uploaded_file.size)
                
                # Store file info in session state for error tracking
                st.session_state.file_uploaded = True
                st.session_state.current_file = {
                    "name": uploaded_file.name,
                    "size": uploaded_file.size,
                    "type": uploaded_file.type
                }
        except Exception as e:
            track_streamlit_error(
                error_type="file_uploader_error",
                error_message=str(e),
                component="file_uploader",
                session_state=st.session_state
            )
            st.error("Error with file upload component")
            uploaded_file = None
            
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            
            # Display file info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024 / 1024:.2f} MB",
                "File type": uploaded_file.type
            }
            
            st.json(file_details)
            
            # Analyze button
            if st.button("🔍 Analyze Track", type="primary"):
                start_time = time.time()
                try:
                    with st.spinner("Analyzing your track..."):
                        # Run analysis
                        analysis_output, temp_path = load_and_analyze_audio(uploaded_file)
                        
                        if analysis_output:
                            # Calculate analysis time
                            analysis_time = time.time() - start_time
                            
                            # Track analysis completion
                            track_analysis_completion(analysis_time, uploaded_file.size)
                            
                            # Store results in session state
                            st.session_state.analysis_results = analysis_output
                            st.session_state.feedback_generated = True
                            
                            # Extract metrics
                            try:
                                metrics = extract_metrics_from_output(analysis_output)
                            except Exception as metrics_error:
                                track_analysis_error(
                                    analysis_step="metrics_extraction",
                                    error_type="metrics_parsing_failed",
                                    error_message=str(metrics_error)
                                )
                                st.error("Error extracting metrics from analysis")
                                return
                            
                            # Track genre detection
                            if vibe_reference:
                                try:
                                    genre_info = analyze_genre_characteristics(metrics.get('tempo', 120), vibe_reference, metrics)
                                    track_genre_detection(genre_info['genre'])
                                except Exception as genre_error:
                                    track_analysis_error(
                                        analysis_step="genre_detection",
                                        error_type="genre_analysis_failed",
                                        error_message=str(genre_error),
                                        metrics=metrics
                                    )
                            
                            # Generate feedback
                            try:
                                feedback_sections = generate_gpt_feedback(metrics, selected_daw, vibe_reference)
                            except Exception as feedback_error:
                                track_analysis_error(
                                    analysis_step="feedback_generation",
                                    error_type="feedback_generation_failed",
                                    error_message=str(feedback_error),
                                    metrics=metrics
                                )
                                st.error("Error generating feedback")
                                return
                            
                            # Store feedback in session state
                            st.session_state.feedback_sections = feedback_sections
                            st.session_state.metrics = metrics
                            
                            st.success("✅ Analysis complete!")
                        else:
                            track_error(
                                error_type="analysis_returned_none",
                                error_message="Analysis function returned None",
                                user_context="analysis_button"
                            )
                            st.error("❌ Analysis failed. Please try again.")
                except Exception as e:
                    track_error(
                        error_type="analysis_button_error",
                        error_message=str(e),
                        user_context="analysis_button"
                    )
                    st.error(f"❌ Unexpected error during analysis: {str(e)}")
    
    with col2:
        st.markdown('<h2 class="sub-header">📈 Quick Stats</h2>', unsafe_allow_html=True)
        
        if st.session_state.analysis_results and st.session_state.metrics:
            metrics = st.session_state.metrics
            
            # Display key metrics
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎵 Tempo</h3>
                <h2>{metrics.get('tempo', 0):.0f} BPM</h2>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>🔊 RMS Level</h3>
                <h2>{metrics.get('rms_db', 0):.1f} dB</h2>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Peak Level</h3>
                <h2>{metrics.get('peak_db', 0):.1f} dB</h2>
            </div>
            """, unsafe_allow_html=True)
            
            dynamic_range = metrics.get('peak_db', 0) - metrics.get('rms_db', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎚️ Dynamic Range</h3>
                <h2>{dynamic_range:.1f} dB</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # Display analysis results
    if st.session_state.analysis_results:
        st.markdown('<h2 class="sub-header">📊 Analysis Results</h2>', unsafe_allow_html=True)
        
        # Show raw analysis output in expander
        with st.expander("🔍 View Raw Analysis Data", expanded=False):
            st.code(st.session_state.analysis_results)
        
        # Visualizations
        if st.session_state.metrics:
            metrics = st.session_state.metrics
            fig_loudness, fig_dynamic = create_visualizations(metrics)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_loudness, use_container_width=True)
            with col2:
                st.plotly_chart(fig_dynamic, use_container_width=True)
    
    # Display feedback
    if st.session_state.feedback_generated and st.session_state.feedback_sections:
        st.markdown('<h2 class="sub-header">🎛️ Professional Mixing Feedback</h2>', unsafe_allow_html=True)
        
        feedback_sections = st.session_state.feedback_sections
        
        # Overall assessment
        with st.expander("🎵 Overall Assessment", expanded=True):
            st.markdown(feedback_sections['overall'])
        
        # Loudness
        with st.expander("🔊 Loudness Analysis", expanded=True):
            st.markdown(feedback_sections['loudness'])
        
        # Clipping
        with st.expander("🎚️ Clipping Analysis", expanded=True):
            st.markdown(feedback_sections['clipping'])
        
        # EQ
        with st.expander("🎛️ EQ Recommendations", expanded=False):
            st.markdown(feedback_sections['eq'])
        
        # Compression
        with st.expander("🎚️ Compression Recommendations", expanded=False):
            st.markdown(feedback_sections['compression'])
        
        # Effects
        with st.expander("✨ Effects Recommendations", expanded=False):
            st.markdown(feedback_sections['effects'])
        
        # Vibe-specific (if provided)
        if vibe_reference and 'vibe' in feedback_sections:
            with st.expander("🎭 Vibe-Specific Recommendations", expanded=False):
                st.markdown(feedback_sections['vibe'])
        
        # Mastering preparation
        with st.expander("🎚️ Mastering Preparation", expanded=False):
            st.markdown(feedback_sections['mastering'])
        
        # Download feedback
        st.markdown("---")
        st.markdown('<h3 class="sub-header">💾 Download Feedback</h3>', unsafe_allow_html=True)
        
        # Create downloadable text
        feedback_text = f"""
MIXBOT - AI Mixing Feedback Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
DAW: {selected_daw}
Vibe/Reference: {vibe_reference if vibe_reference else 'Not specified'}

{'='*50}

"""
        
        for section_name, content in feedback_sections.items():
            feedback_text += f"\n{content}\n"
        
        # Download button
        download_clicked = st.download_button(
            label="📥 Download Feedback Report (.txt)",
            data=feedback_text,
            file_name=f"mixbot_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        # Track download (note: this will track every time the button is rendered)
        # For more accurate tracking, you'd need a custom solution
        if download_clicked:
            track_feedback_download()

if __name__ == "__main__":
    main() 