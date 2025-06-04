# =============================
# 📦 app/routes/case_strategy.py
# =============================
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services import case_strategy
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/case-strategy", response_class=HTMLResponse)
async def form(request: Request):
    return templates.TemplateResponse("case_strategy.html", {"request": request})

@router.post("/case-strategy/process", response_class=HTMLResponse)
async def process(request: Request, files: list[UploadFile] = File(...)):
    case_id = f"case_{uuid.uuid4().hex}"
    docs = case_strategy.parse_documents(files)
    classified = case_strategy.classify_documents(docs)
    timeline = case_strategy.summarize_timeline(classified)
    status = case_strategy.infer_status(timeline)
    steps = case_strategy.recommend_steps(timeline)
    plan = case_strategy.execution_plan(status, steps)
    case_strategy.store_case_vectors(classified, case_id)

    return templates.TemplateResponse("case_strategy_result.html", {
        "request": request,
        "timeline": timeline,
        "status": status,
        "next_steps": steps,
        "plan": plan,
        "case_id": case_id
    })