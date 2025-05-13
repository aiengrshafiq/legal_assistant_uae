from fastapi import APIRouter, UploadFile
from app.services.summarizer import summarize_pdf

router = APIRouter()

@router.post("/api/summarize")
async def summarize_file(file: UploadFile):
    content = await file.read()
    summary = summarize_pdf(content)
    return {"summary": summary}
