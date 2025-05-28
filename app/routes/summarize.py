from fastapi import APIRouter, UploadFile
from app.services.summarizer import summarize_case

from app.auth.utils import log_query, get_current_user
from app.auth.models import User
from fastapi import Depends, Request

router = APIRouter()


@router.post("/api/summarize")
async def summarize_file(request: Request, file: UploadFile, user: User = Depends(get_current_user)):
    file_bytes = await file.read()
    result = summarize_case(file.filename, file_bytes)

    # ✅ Log to database
    log_query(
        user.email,
        user.username,
        "Summarize a Case",
        f"Uploaded file: {file.filename}",
        result
    )

    return {"summary": result}