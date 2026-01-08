import streamlit as st
import librosa
import soundfile as sf
import numpy as np
from scipy.signal import sosfilt
import math
import io

# --- Try to import Rubberband (High Quality), fail gracefully if missing ---
# This allows the app to run locally for testing (low quality)
# but use high quality automatically when deployed to the cloud.
try:
    import pyrubberband as pyrb
    HAS_RUBBERBAND = True
except (ImportError, OSError):
    HAS_RUBBERBAND = False

# --- Configuration ---
st.set_page_config(page_title="Practice Player", page_icon="🎹", layout="centered")

# --- CSS Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f9f9f9; }
    .stButton>button {
        background-color: #4CAF50; color: white; border-radius: 20px; border: none; padding: 10px 24px; width: 100%;
    }
    div[data-testid="stFileUploader"] {
        border: 2px dashed #cccccc; border-radius: 10px; padding: 20px;
    }
    .warning-box {
        background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 10px; border-radius: 5px; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DSP Functions (Audio Processing Logic) ---
def design_high_shelf(cutoff, fs, gain_db, Q=0.707):
    # Standard Audio EQ Cookbook formula for a High Shelf Filter
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * math.pi * cutoff / fs
    alpha = math.sin(w0) / (2 * Q)
    cos_w0 = math.cos(w0)
    b0 = A * ((A + 1) + (A - 1) * cos_w0 + 2 * math.sqrt(A) * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
    b2 = A * ((A + 1) + (A - 1) * cos_w0 - 2 * math.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * cos_w0 + 2 * math.sqrt(A) * alpha
    a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
    a2 = (A + 1) - (A - 1) * cos_w0 - 2 * math.sqrt(A) * alpha
    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0
    # Return as Second-Order Sections for scipy
    return np.array([[b[0], b[1], b[2], a[0], a[1], a[2]]])

def process_audio(file_bytes, filename, speed_rate, pitch_semitones, smoothness_level):
    # Load audio (sr=None keeps original sample rate)
    y, sr = librosa.load(file_bytes, sr=None)

    # --- 1. PITCH & TIME STRETCH ---
    if HAS_RUBBERBAND:
        # HIGH QUALITY MODE (Cloud)
        if pitch_semitones != 0:
            y = pyrb.pitch_shift(y, sr, n_steps=pitch_semitones)
        if speed_rate != 1.0:
            y = pyrb.time_stretch(y, sr, speed_rate)
    else:
        # LOW QUALITY FALLBACK MODE (Local Testing)
        if pitch_semitones != 0:
            y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_semitones)
        if speed_rate != 1.0:
            y = librosa.effects.time_stretch(y, rate=speed_rate)

    # --- 2. CONDITIONAL MP3 FIX (Background) ---
    # Subtle 12kHz cut for MP3s only
    if filename.lower().endswith('.mp3'):
        sos_mp3 = design_high_shelf(cutoff=12000, fs=sr, gain_db=-6.0, Q=0.5)
        y = sosfilt(sos_mp3, y)

    # --- 3. USER SMOOTHING CONTROL ---
    # Adjustable 8kHz cut based on slider position
    if smoothness_level > 0:
        cut_db = -1.0 * smoothness_level 
        sos_smooth = design_high_shelf(cutoff=8000, fs=sr, gain_db=cut_db, Q=0.707)
        y = sosfilt(sos_smooth, y)

    return y, sr

# --- Main UI ---
st.title("🎹 Musician's Slow-Down Tool")

# Check for Engine status for the user
if not HAS_RUBBERBAND:
    st.markdown("""
        <div class="warning-box">
        ⚠️ <b>Running in Standard Mode (Local Testing)</b><br>
        High-Quality audio engine not found on this PC. Audio will sound "grainy" for now.<br>
        <b>Don't worry!</b> When deployed to the Cloud, it will automatically switch to High Quality.
        </div>
    """, unsafe_allow_html=True)
