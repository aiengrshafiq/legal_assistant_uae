# === File: app/routes/litigation_analysis.py ===

from fastapi import APIRouter, Form, UploadFile, File, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.litigation_service import analyze_case

from app.auth.utils import log_query, get_current_user
from fastapi import Depends
from app.auth.models import User


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/litigation-analyze", response_class=HTMLResponse)
async def get_litigation_analysis_page(request: Request):
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
    user: User = Depends(get_current_user)
):
    result = await analyze_case(
        case_title, case_type, jurisdiction, party_roles,
        claim_description, evidence_summary, desired_outcome,
        representation, language, file
    )
    log_query(
        user_email=user.email,
        username=user.username,
        module="Litigation Analysis",
        question=f"Title: {case_title}, Type: {case_type}, Jurisdiction: {jurisdiction}, Claim: {claim_description}",
        response=result
    )
    return JSONResponse(content={"analysis": result})