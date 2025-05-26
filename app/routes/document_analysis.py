# === File: app/routes/document_analysis.py ===

from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.document_service import analyze_legal_document
from app.utils import extract_text_from_upload_all

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/document_analysis", response_class=HTMLResponse)
async def get_document_analysis_page(request: Request):
    return templates.TemplateResponse("document_analysis.html", {"request": request})

@router.post("/api/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    docType: str = Form(""),
    jurisdiction: str = Form("")
):
    content = await file.read()
    try:
        text = extract_text_from_upload_all(file.filename, content)
        result = await analyze_legal_document(text, docType, jurisdiction)
        return JSONResponse(content={"result": result})
    except Exception as e:
        import logging
        logging.exception("❌ Document upload error")
        return JSONResponse(status_code=400, content={"error": str(e)})