# File: app/services/rag.py

import os
import logging
from typing import List, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams
from langchain.schema import Document
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# === OpenAI & Qdrant Setup ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_EN = "uae_law_openai"
COLLECTION_AR = "uae_law_arabert"

qd_client = QdrantClient(url=f"https://{QDRANT_HOST}", api_key=QDRANT_API_KEY)
logger = logging.getLogger("RAG")

def detect_language(text: str) -> str:
    arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
    return "ar" if any(c in arabic_chars for c in text) else "en"

def embed_text(text: str) -> List[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[text]
    )
    return response.data[0].embedding

def search_qdrant(query: str, lang: str, k: int = 10) -> List[Document]:
    embedding = embed_text(query)
    collection = COLLECTION_AR if lang == "ar" else COLLECTION_EN
    try:
        results = qd_client.search(
            collection_name=collection,
            query_vector=embedding,
            limit=k,
            search_params=SearchParams(hnsw_ef=128)
        )
    except Exception as e:
        logger.exception("Qdrant search failed")
        return []

    docs = []
    for hit in results:
        payload = hit.payload or {}
        metadata = {
            "source": payload.get("source", "unknown"),
            "page": payload.get("page", "N/A"),
            "law_name": payload.get("law_name", ""),
            "lang": payload.get("lang", ""),
            "article_number": payload.get("article_number", ""),
            "clause": payload.get("clause", ""),
            "version": payload.get("version", ""),
            "source_url": payload.get("source_url", "")
        }
        content = payload.get("page_content") or payload.get("text", "")
        logger.info(f"QDRANT HIT: {metadata['source']} - Page {metadata['page']}")
        docs.append(Document(page_content=content, metadata=metadata))
    return docs

def compress_chunks_if_needed(docs: List[Document], max_tokens: int = 3000) -> str:
    context = "\n\n".join(doc.page_content for doc in docs)
    if len(context.split()) > max_tokens:
        summary_prompt = f"""Summarize the following legal content:

{context}"""
        summary = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": summary_prompt}]
        ).choices[0].message.content
        return summary
    return context


def needs_clarification(question: str):
    required_keywords = ["jurisdiction", "value", "status"]
    missing = [kw for kw in required_keywords if kw not in question.lower()]
    if missing:
        return f"❌ Please clarify the following before proceeding: {', '.join(missing)}."
    return None

