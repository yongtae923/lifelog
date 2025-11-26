import sqlite3
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os
import time
import datetime

# --- 설정 ---
# backend 폴더 기준 3단계 위가 프로젝트 루트 (~/LifeLog)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'db', 'lifelog.db')
CHROMA_PATH = os.path.join(BASE_DIR, 'db', 'chroma_store')

# --- ChromaDB 초기화 (로컬 저장소) ---
client = chromadb.PersistentClient(path=CHROMA_PATH)

# 다국어 지원 임베딩 모델 (한국어 성능 Good, 로컬 실행)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

# 컬렉션(테이블) 가져오기
collection = client.get_or_create_collection(
    name="screen_logs",
    embedding_function=emb_fn
)

def sync_db_to_chroma():
    """SQLite에 새로 들어온 로그만 ChromaDB로 복사"""
    conn = sqlite3.connect(DB_PATH)
    
    # 1. 이미 저장된 데이터 확인 (가장 마지막 ID 찾기)
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
        return # 새 데이터 없음

    print(f"[{datetime.datetime.now()}] Embedding {len(df)} new logs...")

    documents = []
    metadatas = []
    ids = []

    for _, row in df.iterrows():
        # 2. 검색에 걸릴 '내용' 구성 (풍부한 문맥 생성)
        # 예: "시간: ..., 앱: 크롬, 제목: 유튜브, 내용: ..."
        combined_text = (
            f"Time: {row['timestamp']}, App: {row['app_name']}, "
            f"Title: {row['window_title']}\n"
            f"Content: {row['ocr_text']}\n"
            f"URL: {row['url']}"
        )
        
        # 3. 필터링에 쓸 '메타데이터' 구성 (WiFi/GPS 제거됨)
        meta = {
            "timestamp": str(row['timestamp']),
            "app_name": str(row['app_name']),
            "window_title": str(row['window_title'])[:50], # 너무 길면 잘림 방지
            "url": str(row['url'])[:100]
        }
        
        documents.append(combined_text)
        metadatas.append(meta)
        ids.append(str(row['id']))

    # 4. 배치 단위로 저장 (100개씩)
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
            time.sleep(60) # 1분마다 동기화 확인
    except KeyboardInterrupt:
        print("\nStopping Embedder...")