import streamlit as st
import librosa
import soundfile as sf
import numpy as np
from scipy.signal import sosfilt
import math
import io

# --- Try to import Rubberband (High Quality), fail gracefully if missing ---
try:
    import pyrubberband as pyrb
    HAS_RUBBERBAND = True
except (ImportError, OSError):
    HAS_RUBBERBAND = False

# --- Configuration ---
st.set_page_config(page_title="Practice Player", page_icon="🎹", layout="centered")

# --- CSS Styling (Fixed for Visibility) ---
# We force text to be BLACK (#000000) so it is visible even if your browser is in Dark Mode.
st.markdown("""
    <style>
    .stApp { 
        background-color: #f9f9f9; 
        color: #000000 !important; 
    }
    h1, h2, h3, p, div, span, label {
        color: #000000 !important;
    }
    .stButton>button {
        background-color: #4CAF50; color: white !important; 
        border-radius: 20px; border: none; padding: 10px 24px; width: 100%;
    }
    .warning-box {
        background-color: #fff3cd; border: 1px solid #ffeeba; 
        color: #856404 !important; 
        padding: 10px; border-radius: 5px; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DSP Functions ---
def design_high_shelf(cutoff, fs, gain_db, Q=0.707):
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
    return np.array([[b[0], b[1], b[2], a[0], a[1], a[2]]])

def process_audio(file_bytes, filename, speed_rate, pitch_semitones, smoothness_level):
    y, sr = librosa.load(file_bytes, sr=None)

    # --- 1. PITCH & TIME STRETCH ---
    if HAS_RUBBERBAND:
        if pitch_semitones != 0:
            y = pyrb.pitch_shift(y, sr, n_steps=pitch_semitones)
        if speed_rate != 1.0:
            y = pyrb.time_stretch(y, sr, speed_rate)
    else:
        # Fallback for local testing
        if pitch_semitones != 0:
            y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_semitones)
        if speed_rate != 1.0:
            y = librosa.effects.time_stretch(y, rate=speed_rate)

    # --- 2. CONDITIONAL MP3 FIX ---
    if filename.lower().endswith('.mp3'):
        sos_mp3 = design_high_shelf(cutoff=12000, fs=sr, gain_db=-6.0, Q=0.5)
        y = sosfilt(sos_mp3, y)

    # --- 3. USER SMOOTHING ---
    if smoothness_level > 0:
        cut_db = -1.0 * smoothness_level 
        sos_smooth = design_high_shelf(cutoff=8000, fs=sr, gain_db=cut_db, Q=0.707)
        y = sosfilt(sos_smooth, y)

    return y, sr

# --- Main UI ---
st.title("🎹 Musician's Slow-Down Tool")

if not HAS_RUBBERBAND:
    st.markdown("""
        <div class="warning-box">
        ⚠️ <b>Standard Mode Active</b><br>
        High-Quality engine missing. If you are seeing this on the Cloud, check packages.txt.
        </div>
    """, unsafe_allow_html=True)

if 'processed_audio' not in st.session_state:
    st.session_state.processed_audio = None
if 'processed_name' not in st.session_state:
    st.session_state.processed_name = ""
if 'last_uploaded' not in st.session_state:
    st.session_state.last_uploaded = ""

uploaded_file = st.file_uploader("Drop your MP3 or WAV here", type=["mp3", "wav"])

if uploaded_file is not None:
    if st.session_state.last_uploaded != uploaded_file.name:
        st.session_state.processed_audio = None
        st.session_state.last_uploaded = uploaded_file.name

    st.audio(uploaded_file, format='audio/wav')
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🐢 Playback Speed")
        speed = st.slider("Playback Rate", 0.25, 1.0, 0.75, 0.05)
    with col2:
        st.subheader("🔧 Pitch Tuning")
        pitch = st.slider("Semitones", -1.0, 1.0, 0.0, 0.05)
    with col3:
        st.subheader("✨ Smoothness Filter")
        smoothness = st.slider("De-Grain Level", 0, 10, 3, 1)

    if uploaded_file.name.lower().endswith('.mp3'):
        st.caption("ℹ️ MP3 detected: Auto-applying extra artifact reduction.")

    st.markdown("---")
    
    if st.button("Generate Practice Track"):
        engine_name = "High Quality Engine" if HAS_RUBBERBAND else "Standard Engine"
        with st.spinner(f"Processing with {engine_name}..."):
            try:
                processed_y, sr = process_audio(
                    uploaded_file, uploaded_file.name, speed, pitch, smoothness
                )
                
                buffer = io.BytesIO()
                sf.write(buffer, processed_y, sr, format='WAV')
                buffer.seek(0)
                
                st.session_state.processed_audio = buffer
                st.session_state.processed_name = f"slow_{uploaded_file.name.rsplit('.', 1)[0]}.wav"
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.processed_audio is not None:
        st.success("Track ready!")
        st.markdown("### 🎧 Result")
        st.audio(st.session_state.processed_audio, format='audio/wav')
        
        st.download_button(
            label="⬇️ Download WAV",
            data=st.session_state.processed_audio,
            file_name=st.session_state.processed_name,
            mime="audio/wav"
        )
