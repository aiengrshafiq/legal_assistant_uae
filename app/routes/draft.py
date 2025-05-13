from fastapi import APIRouter, UploadFile, Form
from app.services.drafter import generate_draft

router = APIRouter()

@router.post("/api/draft")
async def draft_file(file: UploadFile, draft_type: str = Form(...)):
    content = await file.read()
    result = generate_draft(content, draft_type)
    return {"draft": result}
