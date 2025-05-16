# Folder: routes/litigation_analysis.py
from fastapi import APIRouter, Form, UploadFile, File, Request
from fastapi.responses import JSONResponse,HTMLResponse
from app.services.litigation_service import analyze_case
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/litigation-analyze", response_class=HTMLResponse)
async def get_legal_research(request: Request):
    return templates.TemplateResponse("litigation.html", {"request": request})

@router.post("/api/litigation-analyze")
async def litigation_analysis_route(
    case_title: str = Form(...),
    case_type: str = Form(...),
    jurisdiction: str = Form(...),
    party_roles: str = Form(...),
    claim_description: str = Form(...),
    evidence_summary: str = Form(...),
    desired_outcome: str = Form(...),
    representation: str = Form(...),
    language: str = Form("en"),
    file: UploadFile = File(None),
):
    result = await analyze_case(
        case_title, case_type, jurisdiction, party_roles,
        claim_description, evidence_summary, desired_outcome,
        representation, language, file
    )
    return JSONResponse(content={"analysis": result})
