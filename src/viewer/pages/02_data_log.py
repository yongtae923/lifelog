import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

st.title("📋 Raw Data Log")
with st.sidebar:
    hours = st.slider("Time Range", 1, 72, 24)
    if st.button("Refresh"): st.cache_data.clear()
df = utils.load_data(hours).sort_values('timestamp', ascending=False)

if not df.empty:
    cols = ['timestamp', 'app_name', 'audio_db', 'url', 'window_title', 'ocr_text']
    st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, height=800)