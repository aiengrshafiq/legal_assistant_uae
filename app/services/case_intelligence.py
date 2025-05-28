from app.utils import extract_text_from_upload_all
from datetime import datetime
import re
from app.services.rag import get_rag_response
from datetime import datetime
from typing import List
import docx
import io
import dateparser

# def extract_date_from_text(text: str):
#     """
#     Extracts the first date found in the document using dateparser.
#     """
#     # You can fine-tune this based on your expected patterns
#     lines = text.split("\n")
#     for line in lines:
#         parsed = dateparser.parse(line, settings={"PREFER_DATES_FROM": "past"})
#         if parsed:
#             return parsed
#     return None  # No date found

def extract_date_from_text(text: str):
    lines = [l for l in text.split("\n") if any(kw in l.lower() for kw in ['date', 'hearing', 'judgment', 'order', 'filed'])]
    for line in lines:
        parsed = dateparser.parse(line, settings={"PREFER_DATES_FROM": "past"})
        if parsed:
            return parsed
    return None

def parse_documents(files) -> List[dict]:
    parsed_docs = []
    for file in files:
        if file.filename.endswith('.pdf') or file.filename.endswith('.txt'):
            content = extract_text_from_upload_all(file.filename, file.file.read())
        elif file.filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file.file.read()))
            content = "\n".join(para.text for para in doc.paragraphs)
        else:
            continue

        date = extract_date_from_text(content)
        parsed_docs.append({
            "filename": file.filename,
            "content": content,
            "date": date,
            "type": "unclassified"
        })
    return parsed_docs


def classify_documents(docs):
    for doc in docs:
        content_lower = doc["content"].lower()
        if "court" in content_lower:
            doc["type"] = "court filing"
        elif "contract" in content_lower:
            doc["type"] = "contract"
        elif "email" in content_lower or "correspondence" in content_lower:
            doc["type"] = "correspondence"
        else:
            doc["type"] = "misc"
    return sorted(docs, key=lambda x: x["date"] or datetime.min)

def summarize_timeline(docs):
    summaries = []
    for doc in docs:
        summary = get_rag_response(doc["content"], tags=["timeline-summary"])
        summaries.append({
            "filename": doc["filename"],
            "summary": summary,
            "date": doc["date"],
            "type": doc["type"]
        })
    return summaries

def infer_case_status(timeline_summaries):
    events_text = "\n".join(f"{e['date']}: {e['summary']}" for e in timeline_summaries)
    return get_rag_response(events_text, tags=["case-status-inference"])

def recommend_next_steps(timeline_summaries):
    context = "\n".join(e['summary'] for e in timeline_summaries)
    return get_rag_response(context, tags=["legal-next-steps"])

def generate_execution_plan(status, next_steps):
    prompt = f"Case status: {status}\nNext Steps: {next_steps}"
    return get_rag_response(prompt, tags=["execution-plan"])
