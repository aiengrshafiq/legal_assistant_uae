from fastapi import APIRouter, UploadFile
from app.services.summarizer import summarize_case

router = APIRouter()

@router.post("/api/summarize")
async def summarize_file(file: UploadFile):
    file_bytes = await file.read()
    result = summarize_case(file.filename, file_bytes)
    return {"summary": result}