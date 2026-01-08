# --- CSS Styling (Fixed for Dropzone Visibility) ---
st.markdown("""
    <style>
    /* Force the main app background to white and text to black */
    .stApp { 
        background-color: #ffffff !important; 
        color: #000000 !important; 
    }
    
    /* Force all headings and text to black */
    h1, h2, h3, p, div, span, label, li {
        color: #000000 !important;
    }
    
    /* TARGET THE FILE UPLOADER specifically to be Light Mode */
    [data-testid="stFileUploader"] {
        background-color: #f0f2f6 !important; /* Light grey background */
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Force text inside the uploader to be black */
    [data-testid="stFileUploader"] div, 
    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] small {
        color: #000000 !important;
        background-color: transparent !important;
    }

    /* Green Buttons */
    .stButton>button {
        background-color: #4CAF50 !important; 
        color: white !important; 
        border-radius: 20px; 
        border: none; 
        padding: 10px 24px; 
        width: 100%;
    }

    /* Warning Box */
    .warning-box {
        background-color: #fff3cd; 
        border: 1px solid #ffeeba; 
        color: #856404 !important; 
        padding: 10px; 
        border-radius: 5px; 
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)
