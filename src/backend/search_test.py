import chromadb
from chromadb.utils import embedding_functions
import os

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_PATH = os.path.join(BASE_DIR, 'db', 'chroma_store')

# DB 연결
client = chromadb.PersistentClient(path=CHROMA_PATH)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
collection = client.get_collection(name="screen_logs", embedding_function=emb_fn)

def search(query_text, n=3):
    print(f"\n🧠 Thinking... searching for '{query_text}'")
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n
    )
    
    if not results['ids'][0]:
        print("검색 결과가 없습니다.")
        return

    for i in range(len(results['ids'][0])):
        score = results['distances'][0][i] # 거리(작을수록 유사함)
        meta = results['metadatas'][0][i]
        doc = results['documents'][0][i]
        
        print(f"\n--- [Result {i+1}] (Distance: {score:.4f}) ---")
        print(f"🕒 {meta['timestamp']} | 📱 {meta['app_name']}")
        print(f"📄 {meta['window_title']}")
        print(f"🔗 {meta['url']}")
        # 본문은 길니까 앞부분만
        print(f"📝 {doc.split('Content: ')[1][:100].replace(chr(10), ' ')}...")

if __name__ == "__main__":
    print("--- LifeLog Search Engine ---")
    while True:
        q = input("\n검색어를 입력하세요 (q:종료) >> ")
        if q.lower() == 'q': break
        try:
            search(q)
        except Exception as e:
            print(f"Error: {e}")
            print("아직 데이터가 없거나 ChromaDB가 생성되지 않았을 수 있습니다.")