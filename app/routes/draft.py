from fastapi import APIRouter, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.drafter import generate_draft

from fastapi.responses import JSONResponse, StreamingResponse
from app.services.drafter import generate_draft, generate_pdf_from_text
from io import BytesIO

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

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
    content = await file.read() if file else description.encode()

    try:
        draft = generate_draft(content, draft_type, language, recipient_name, recipient_contact, instructions)
        if not draft.strip():
            raise ValueError("Draft text is empty")

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
        else:
            return JSONResponse(content={"draft": draft})

    except Exception as e:
        print("[❌ ERROR] Failed to generate draft:", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Draft generation failed. Please check the uploaded content and try again."}
        )

