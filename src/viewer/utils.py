import streamlit as st
import sqlite3
import pandas as pd
import os
import datetime
import re
from wordcloud import WordCloud

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'db', 'lifelog.db')

@st.cache_data(ttl=60)
def load_data(hours_back):
    if not os.path.exists(DB_PATH): return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    time_threshold = (datetime.datetime.now() - datetime.timedelta(hours=hours_back)).strftime('%Y-%m-%d %H:%M:%S')
    try:
        df = pd.read_sql_query(f"SELECT * FROM screen_logs WHERE timestamp > '{time_threshold}' ORDER BY timestamp ASC", conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except: df = pd.DataFrame()
    conn.close()
    return df

def generate_wordcloud_img(text_series):
    full_text = " ".join(text_series.dropna().astype(str))
    words = re.findall(r'[가-힣a-zA-Z]{2,}', full_text)
    clean_string = " ".join(words)
    if not clean_string.strip(): return None
    
    font_path = '/System/Library/Fonts/Supplemental/AppleGothic.ttf'
    if not os.path.exists(font_path): font_path = None
    
    return WordCloud(width=800, height=400, background_color='white', font_path=font_path,
                     colormap='plasma', margin=5).generate(clean_string)