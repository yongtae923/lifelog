import time
import sqlite3
import os
import datetime
import subprocess
import shutil
import numpy as np
import sounddevice as sd
from PIL import Image
import pytesseract

# --- Configuration (project root is three levels up from this file) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'db', 'lifelog.db')
TEMP_SCREENSHOT_PATH = os.path.join(BASE_DIR, 'logs', 'temp_screen.png')

# Configure the Tesseract binary path
tesseract_cmd_path = shutil.which('tesseract')
if tesseract_cmd_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
else:
    possible_paths = ['/opt/homebrew/bin/tesseract', '/usr/local/bin/tesseract']
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

# --- Database initialization ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screen_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            app_name TEXT,
            window_title TEXT,
            ocr_text TEXT,
            url TEXT,
            audio_db REAL
        )
    ''')
    conn.commit()
    conn.close()

# --- Sensor helper functions ---
def get_browser_url(app_name):
    if app_name not in ["Google Chrome", "Safari", "Arc"]: return ""
    script = ""
    if app_name == "Google Chrome": script = 'tell application "Google Chrome" to return URL of active tab of front window'
    elif app_name == "Safari": script = 'tell application "Safari" to return URL of front document'
    elif app_name == "Arc": script = 'tell application "Arc" to return URL of active tab of front window'
    try: return subprocess.check_output(['osascript', '-e', script], stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except: return ""

def get_audio_level(duration=2):
    try:
        recording = sd.rec(int(duration * 44100), samplerate=44100, channels=1, dtype='float64')
        sd.wait()
        rms = np.sqrt(np.mean(recording**2))
        db_fs = 20 * np.log10(rms) if rms > 0 else -99.0
        noise_score = int((db_fs + 60) * 2.5)
        return max(0, min(100, noise_score))
    except: return 0

def get_active_window_info():
    try:
        script = '''
        global frontApp, frontAppName, windowTitle
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            try
                set windowTitle to name of window 1 of frontApp
            on error
                set windowTitle to ""
            end try
        end tell
        return frontAppName & "\n" & windowTitle
        '''
        result = subprocess.check_output(['osascript', '-e', script]).decode('utf-8').strip()
        if result:
            parts = result.split('\n')
            return parts[0], parts[1] if len(parts) > 1 else ""
    except: pass
    return "Unknown", "Unknown"

# --- Main loop ---
def capture_and_log():
    try:
        subprocess.run(['screencapture', '-x', TEMP_SCREENSHOT_PATH], check=True)
        text = ""
        if os.path.exists(TEMP_SCREENSHOT_PATH):
            text = pytesseract.image_to_string(Image.open(TEMP_SCREENSHOT_PATH), lang='kor+eng').strip()
        
        app_name, window_title = get_active_window_info()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        url = get_browser_url(app_name)
        audio_score = get_audio_level(duration=2)
        
        if text or app_name != "Unknown":
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO screen_logs 
                (timestamp, app_name, window_title, ocr_text, url, audio_db)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (now, app_name, window_title, text, url, audio_score))
            conn.commit()
            conn.close()
            
            print(f"[{now}] App:{app_name} | Noise:{audio_score}")
        
        if os.path.exists(TEMP_SCREENSHOT_PATH):
            os.remove(TEMP_SCREENSHOT_PATH)
    except Exception as e:
        print(f"Log Error: {e}")

if __name__ == "__main__":
    print(f"--- LifeLogger (Backend: Logger) ---")
    init_db()
    try:
        while True:
            capture_and_log()
            time.sleep(180) 
    except KeyboardInterrupt:
        print("\nStopping...")