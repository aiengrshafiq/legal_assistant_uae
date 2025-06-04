# ================================
# 📦 app/services/case_strategy.py
# ================================
import io, uuid, docx
from typing import List
from datetime import datetime
from app.utils import extract_text_from_upload_all, extract_text_with_ocr
from app.services.rag import get_rag_response
from app.qachain import store_case_chunks_to_qdrant
import dateparser
import uuid


def extract_date(text: str):
    for line in text.split("\n"):
        if any(k in line.lower() for k in ['date', 'hearing', 'judgment', 'filed', 'order']):
            parsed = dateparser.parse(line, settings={"PREFER_DATES_FROM": "past"})
            if parsed:
                return parsed
    return None

def parse_documents(files) -> List[dict]:
    parsed_docs = []
    for file in files:
        content = extract_text_with_ocr(file.file.read(), file.filename)
        date = extract_date(content)
        parsed_docs.append({
            "filename": file.filename,
            "content": content,
            "date": date,
            "type": "unclassified"
        })
    return parsed_docs

def classify_documents(docs):
    for doc in docs:
        text = doc["content"].lower()
        if "court" in text:
            doc["type"] = "court filing"
        elif "contract" in text:
            doc["type"] = "contract"
        elif "correspondence" in text or "email" in text:
            doc["type"] = "correspondence"
        else:
            doc["type"] = "misc"
    return sorted(docs, key=lambda d: d["date"] or datetime.min)

def summarize_timeline(docs):
    return [{
        "filename": d["filename"],
        "summary": get_rag_response(d["content"], tags=["timeline-summary"]),
        "date": d["date"],
        "type": d["type"]
    } for d in docs]

def infer_status(summaries):
    text = "\n".join(f"{s['date']}: {s['summary']}" for s in summaries)
    return get_rag_response(text, tags=["case-status-inference"])

def recommend_steps(summaries):
    text = "\n".join(s['summary'] for s in summaries)
    return get_rag_response(text, tags=["legal-next-steps"])

def execution_plan(status, steps):
    return get_rag_response(
        f"Case status: {status}\nNext Steps: {steps}", tags=["execution-plan"]
    )

def store_case_vectors(docs, case_id):
    for doc in docs:
        store_case_chunks_to_qdrant(doc['content'], namespace=case_id)




