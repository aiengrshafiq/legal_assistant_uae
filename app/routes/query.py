from fastapi import APIRouter, Request
from app.services.rag import ask_question

router = APIRouter()

from pydantic import BaseModel
from typing import List, Optional

class SourceItem(BaseModel):
    filename: str
    page: str
    excerpt: str

class QueryResponse(BaseModel):
    short_answer: str
    detailed_answer: Optional[str] = ""
    sources: List[SourceItem]

@router.post("/api/query", response_model=QueryResponse)
async def handle_query(request: Request):
    data = await request.json()
    question = data.get("question")
    result = ask_question(question)
    return {
        "short_answer": result.get("short_answer", ""),
        "detailed_answer": result.get("detailed_answer", ""),
        "sources": result.get("sources", [])
    }