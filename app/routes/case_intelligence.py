from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services import case_intelligence

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/case-intelligence", response_class=HTMLResponse)
async def case_upload_form(request: Request):
    return templates.TemplateResponse("case_intelligence.html", {"request": request})

@router.post("/case-intelligence/process", response_class=HTMLResponse)
async def process_case(request: Request, files: list[UploadFile] = File(...)):
    parsed = case_intelligence.parse_documents(files)
    classified = case_intelligence.classify_documents(parsed)
    timeline = case_intelligence.summarize_timeline(classified)
    status = case_intelligence.infer_case_status(timeline)
    next_steps = case_intelligence.recommend_next_steps(timeline)
    plan = case_intelligence.generate_execution_plan(status, next_steps)

    return templates.TemplateResponse("case_intelligence_result.html", {
        "request": request,
        "timeline": timeline,
        "status": status,
        "next_steps": next_steps,
        "plan": plan
    })
