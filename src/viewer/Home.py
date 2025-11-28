import streamlit as st
import utils
import plotly.express as px
import matplotlib.pyplot as plt

st.set_page_config(page_title="My LifeLog", page_icon="📊", layout="wide")
st.title("📊 Activity Dashboard")

with st.sidebar:
    hours = st.slider("Time Range", 1, 72, 24)
    if st.button("Refresh"): st.cache_data.clear()

df = utils.load_data(hours)
if df.empty:
    st.warning("No Data Found.")
    st.stop()

# Key metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total Logs", len(df))
c2.metric("Used Apps", df['app_name'].nunique())
c3.metric("Avg Noise", int(df['audio_db'].mean()) if 'audio_db' in df.columns else 0)

st.divider()

# Activity timeline
st.subheader("📈 Activity Flow")
df_res = df.set_index('timestamp').resample('10T').size().reset_index(name='count')
fig = px.line(df_res, x='timestamp', y='count')
fig.update_traces(fill='tozeroy', line_color='#4C78A8')
fig.update_layout(height=300, dragmode='select', hovermode='x unified')
selection = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

# App ranking & word cloud
col_l, col_r = st.columns(2)
with col_l:
    st.subheader("🏆 Top Apps")
    cnt = df['app_name'].value_counts().head(10).reset_index(name='count')
    
    # 1. Build the chart object first.
    fig = px.bar(
        cnt, 
        y='app_name', 
        x='count', 
        orientation='h', 
        color='count', 
        color_continuous_scale='Viridis'
    )
    
    # 2. Reorder the Y axis so the largest value appears at the top.
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    
    # 3. Render the chart
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.subheader("☁️ Context Word Cloud")
    sel_txt = df['ocr_text']
    if selection and selection['selection'].get('range'):
        xr = selection['selection']['range']['x']
        sel_txt = df[(df['timestamp']>=xr[0])&(df['timestamp']<=xr[1])]['ocr_text']
    
    img = utils.generate_wordcloud_img(sel_txt)
    if img:
        fig_wc, ax = plt.subplots(figsize=(8,5))
        ax.imshow(img, interpolation='bilinear'); ax.axis('off')
        st.pyplot(fig_wc)
    else: st.info("No text data")

st.divider()

# Noise Level Distribution
st.subheader("🎧 Noise Level Distribution")
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

st.divider()

# Top Domains
st.subheader("🔗 Top Domains")
if 'url' in df.columns:
    df['domain'] = df['url'].apply(lambda x: x.split('/')[2] if isinstance(x,str) and len(x)>8 else None)
    cnt_domain = df['domain'].value_counts().reset_index(name='count')
    if not cnt_domain.empty:
        st.plotly_chart(px.treemap(cnt_domain.head(20), path=['domain'], values='count'), use_container_width=True)

st.divider()

# Raw Data Log
st.subheader("📋 Raw Data Log")
df_sorted = df.sort_values('timestamp', ascending=False)
if not df_sorted.empty:
    cols = ['timestamp', 'app_name', 'audio_db', 'url', 'window_title', 'ocr_text']
    st.dataframe(df_sorted[[c for c in cols if c in df_sorted.columns]], use_container_width=True, height=600)