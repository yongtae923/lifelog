# LifeLog

A personal life-logging stack that captures macOS screen context (active app, OCR text, audio noise) and visualizes recent activity through Streamlit dashboards.

## Features
- **Backend logger** (`src/backend/logger.py`): captures screenshots, runs OCR (Tesseract), logs active app/window, browser URL, and ambient noise level every 5 minutes into `db/lifelog.db`.
- **Embeddings pipeline** (`src/backend/embedder.py`): syncs textual context to a local ChromaDB vector store for semantic search experiments.
- **Viewer app** (`src/viewer/Home.py`): single-page dashboard with overview metrics, activity timeline, top apps, word cloud, deep analysis tabs (Noise Distribution, Top Domains), and raw data log table.

## Prerequisites
- macOS (uses `screencapture`, `osascript`, CoreAudio, etc.)
- [conda](https://docs.conda.io/en/latest/miniconda.html) (recommended)
- Xcode command line tools (`xcode-select --install`)
- Tesseract OCR (`brew install tesseract`)

## Conda Environment Setup

```bash
cd /Users/Amwoo/LifeLog

# create environment
conda create -n lifelog python=3.11 -y
conda activate lifelog

# install python deps
pip install -r requirements.txt  # create this file if missing, otherwise install manually:
pip install streamlit plotly matplotlib pandas numpy sounddevice Pillow pytesseract wordcloud chromadb

# optional dev tools
pip install black isort mypy
```

> **Tip:** If `sounddevice` installation fails, ensure `portaudio` is installed (`brew install portaudio`) before retrying.

## Local Database Initialization

```bash
python src/backend/logger.py --init-db  # or simply run once; init_db() auto-executes
```

The logger stores data in `db/lifelog.db` (ignored by git). Logs and screenshots live under `logs/`.

## Running the Backend Logger

```bash
conda activate lifelog
python src/backend/logger.py
```

The script loops forever (Ctrl+C to stop) and captures every ~5 minutes.

## Running the Streamlit Viewer

```bash
conda activate lifelog
cd src/viewer
streamlit run Home.py
```

The sidebar lets you adjust time range and force-refresh cached queries. All visualizations and tables update based on the selected time window.

## macOS Installation & Launch Instructions

1. **Get the code**
   ```bash
   git clone <repo-url> ~/LifeLog   # or copy manually
   cd ~/LifeLog
   ```
2. **Install dependencies**
   ```bash
   conda create -n lifelog python=3.11 -y
   conda activate lifelog
   pip install -r requirements.txt
   brew install tesseract portaudio
   ```
3. **Verify components manually**
   ```bash
   python src/backend/logger.py
   python src/backend/embedder.py
   streamlit run src/viewer/Home.py
   ```
4. **Optional: run via LaunchAgents for auto start**
   - Create plist files: `~/Library/LaunchAgents/com.amwoo.lifelog.plist`, `com.amwoo.lifelog.embedder.plist`, `com.amwoo.lifelog.viewer.plist`.
   - Load them:
     ```bash
     launchctl load -w ~/Library/LaunchAgents/com.amwoo.lifelog.plist
     launchctl load ~/Library/LaunchAgents/com.amwoo.lifelog.embedder.plist
     launchctl load ~/Library/LaunchAgents/com.amwoo.lifelog.viewer.plist
     ```
   - You can still launch the viewer manually:
     ```bash
     streamlit run ~/LifeLog/src/viewer/Home.py
     ```

## Repository Notes
- `logs/`, `db/*.db`, and other machine-specific files are already in `.gitignore`.
- This repo is intended for local personal use; no remote configured by default.

Feel free to adapt the capture interval, visualization logic, or search experiments to your workflow. Contributions (even personal forks) are welcome—just remember this project touches privacy-sensitive data, so keep it local unless you remove personal logs.

