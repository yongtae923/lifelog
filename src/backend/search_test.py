import chromadb
from chromadb.utils import embedding_functions
import os

# Resolve project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_PATH = os.path.join(BASE_DIR, 'db', 'chroma_store')

# Connect to ChromaDB
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
        print("No results found.")
        return

    for i in range(len(results['ids'][0])):
        score = results['distances'][0][i] # Distance (smaller means more similar)
        meta = results['metadatas'][0][i]
        doc = results['documents'][0][i]
        
        print(f"\n--- [Result {i+1}] (Distance: {score:.4f}) ---")
        print(f"🕒 {meta['timestamp']} | 📱 {meta['app_name']}")
        print(f"📄 {meta['window_title']}")
        print(f"🔗 {meta['url']}")
        # Print only the beginning because the body can be long
        print(f"📝 {doc.split('Content: ')[1][:100].replace(chr(10), ' ')}...")

if __name__ == "__main__":
    print("--- LifeLog Search Engine ---")
    while True:
        q = input("\nEnter a search query (q to quit) >> ")
        if q.lower() == 'q': break
        try:
            search(q)
        except Exception as e:
            print(f"Error: {e}")
            print("Data may be missing or the ChromaDB store might not exist yet.")