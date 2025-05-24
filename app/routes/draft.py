from fastapi import APIRouter, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.services.drafter import generate_legal_draft, generate_pdf_from_text
from io import BytesIO
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("draft")

@router.get("/generate-draft", response_class=HTMLResponse)
async def draft_page(request: Request):
    return templates.TemplateResponse("generate_draft.html", {"request": request})

@router.post("/api/draft")
async def draft_file(
    file: UploadFile = None,
    description: str = Form(None),
    draft_type: str = Form(...),
    language: str = Form(...),
    recipient_name: str = Form(""),
    recipient_contact: str = Form(""),
    instructions: str = Form(""),
    as_pdf: bool = Form(False)
):
    try:
        file_bytes = await file.read() if file else None

        draft = generate_legal_draft(
            file_bytes=file_bytes,
            description=description,
            draft_type=draft_type,
            language=language,
            recipient=recipient_name,
            contact=recipient_contact,
            instructions=instructions
        )

        if not draft.strip():
            raise ValueError("Draft is empty")

        if as_pdf:
            pdf_bytes = generate_pdf_from_text(draft)
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={draft_type.replace(' ', '_')}_draft.pdf",
                    "Content-Length": str(len(pdf_bytes))
                }
            )

        return JSONResponse(content={"draft": draft})

    except Exception as e:
        logger.exception("❌ Draft generation failed")
        return JSONResponse(
            status_code=500,
            content={"error": "Draft generation failed. Please check the inputs and try again."}
        )
