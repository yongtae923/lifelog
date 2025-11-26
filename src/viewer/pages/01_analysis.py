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
    custom_colors = {
        "Arc": "#4FC3F7",               # sky blue
        "Obsidian": "#8E44AD",          # purple
        "KakaoTalk": "#FEE500",         # yellow
        "Discord": "#1B1F72",           # navy
        "Microsoft Word": "#185ABD",    # blue
        "Cursor": "#9AA0A6",            # gray
    }
    scatter_fig = px.scatter(
        df,
        x='timestamp',
        y='audio_db',
        color='app_name',
        size='audio_db',
        color_discrete_map=custom_colors,
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    st.plotly_chart(scatter_fig, use_container_width=True)

with t2:
    st.subheader("Top Domains")
    if 'url' in df.columns:
        df['domain'] = df['url'].apply(lambda x: x.split('/')[2] if isinstance(x,str) and len(x)>8 else None)
        cnt = df['domain'].value_counts().reset_index(name='count')
        if not cnt.empty:
            st.plotly_chart(px.treemap(cnt.head(20), path=['domain'], values='count'), use_container_width=True)