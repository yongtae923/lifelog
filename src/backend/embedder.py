import sqlite3
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os
import time
import datetime

# --- Settings ---
# Project root is three levels up from this backend folder (~/LifeLog)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'db', 'lifelog.db')
CHROMA_PATH = os.path.join(BASE_DIR, 'db', 'chroma_store')

# --- Initialize ChromaDB (local persistent store) ---
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Multilingual embedding model (solid Korean performance, runs locally)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

# Fetch or create the collection/table
collection = client.get_or_create_collection(
    name="screen_logs",
    embedding_function=emb_fn
)

def sync_db_to_chroma():
    """Copy only the new SQLite rows into ChromaDB."""
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Determine the last indexed ID to fetch only new rows.
    existing_ids = collection.get()['ids']
    if existing_ids:
        max_id = max([int(i) for i in existing_ids])
        query = f"SELECT * FROM screen_logs WHERE id > {max_id}"
    else:
        query = "SELECT * FROM screen_logs"
    
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"DB Error: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    
    if df.empty:
        return # No new data

    print(f"[{datetime.datetime.now()}] Embedding {len(df)} new logs...")

    documents = []
    metadatas = []
    ids = []

    for _, row in df.iterrows():
        # 2. Build the searchable document text with rich context.
        # Example: "Time: ..., App: Chrome, Title: YouTube, Content: ..."
        combined_text = (
            f"Time: {row['timestamp']}, App: {row['app_name']}, "
            f"Title: {row['window_title']}\n"
            f"Content: {row['ocr_text']}\n"
            f"URL: {row['url']}"
        )
        
        # 3. Build metadata used for filtering (WiFi/GPS removed)
        meta = {
            "timestamp": str(row['timestamp']),
            "app_name": str(row['app_name']),
            "window_title": str(row['window_title'])[:50], # Prevent extremely long values
            "url": str(row['url'])[:100]
        }
        
        documents.append(combined_text)
        metadatas.append(meta)
        ids.append(str(row['id']))

    # 4. Persist in batches (100 entries at a time)
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        end = i + batch_size
        collection.add(
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            ids=ids[i:end]
        )
    
    print(f"Done! Synced {len(documents)} logs.")

if __name__ == "__main__":
    print(f"--- LifeLog Embedder (Syncing SQLite -> ChromaDB) ---")
    print(f"DB: {DB_PATH}")
    print(f"Vector DB: {CHROMA_PATH}")
    
    try:
        while True:
            sync_db_to_chroma()
            time.sleep(60) # Check for new data every minute
    except KeyboardInterrupt:
        print("\nStopping Embedder...")