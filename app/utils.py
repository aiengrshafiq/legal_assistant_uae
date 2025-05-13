import os
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# === OpenAI & Qdrant Configuration ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_EN = "uae_law_openai"
COLLECTION_AR = "uae_law_arabert"

qd_client = QdrantClient(
    url=f"https://{os.getenv('QDRANT_HOST')}",
    api_key=os.getenv("QDRANT_API_KEY"),
)


# === Custom Document Class ===
class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}


def extract_keywords(text: str) -> str:
    # Simple heuristic: return first 1–2 sentences as pseudo-query
    sentences = text.strip().split(".")
    return ". ".join(sentences[:2]).strip()
    
# === Language Detection ===
def detect_language(text: str) -> str:
    arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
    if any(c in arabic_chars for c in text):
        return "ar"
    return "en"

# === OpenAI Embedding ===
def embed_text(text: str) -> List[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",  # or "text-embedding-ada-002"
        input=[text]
    )
    return response.data[0].embedding

# === Qdrant Semantic Search ===
def direct_qdrant_search(query: str, lang: str = "en", k: int = 10) -> List[Document]:
    embedding = embed_text(query)
    collection_name = COLLECTION_AR if lang == "ar" else COLLECTION_EN

    try:
        search_result = qd_client.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=k,
            search_params=SearchParams(hnsw_ef=128),
        )
    except Exception as e:
        print(f"[QDRANT ERROR] {e}")
        return []

    docs = []
    for hit in search_result:
        payload = hit.payload or {}
        content = payload.get("page_content") or payload.get("text", "")
        print(f"[QDRANT HIT] {payload.get('source')} | Preview: {content[:100]}")
        metadata = {
            "source": payload.get("source", "unknown"),
            "page": payload.get("page", "N/A"),
        }
        docs.append(Document(page_content=content, metadata=metadata))

    return docs
