from fastapi import APIRouter, Request
from app.services.rag import ask_question

router = APIRouter()

@router.post("/api/query")
async def handle_query(request: Request):
    data = await request.json()
    question = data.get("question")
    result = ask_question(question)
    return result

