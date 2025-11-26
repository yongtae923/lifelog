import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

st.title("🔍 Deep Analysis")
hours = st.sidebar.slider("Time Range", 1, 72, 24)
df = utils.load_data(hours)
if df.empty: st.stop()

t1, t2 = st.tabs(["🎧 Noise", "🔗 URL"])

with t1:
    st.subheader("Noise Level Distribution")
    st.plotly_chart(px.scatter(df, x='timestamp', y='audio_db', color='app_name', size='audio_db'), use_container_width=True)

with t2:
    st.subheader("Top Domains")
    if 'url' in df.columns:
        df['domain'] = df['url'].apply(lambda x: x.split('/')[2] if isinstance(x,str) and len(x)>8 else None)
        cnt = df['domain'].value_counts().reset_index(name='count')
        if not cnt.empty:
            st.plotly_chart(px.treemap(cnt.head(20), path=['domain'], values='count'), use_container_width=True)