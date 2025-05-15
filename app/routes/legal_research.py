# File: app/routes/legal_research.py
from fastapi import APIRouter, Request, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.research_service import process_legal_research

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/legal-research", response_class=HTMLResponse)
async def get_legal_research(request: Request):
    return templates.TemplateResponse("legal_research.html", {"request": request})

@router.post("/legal-research")
async def post_legal_research(
    request: Request,
    topic: str = Form(...),
    jurisdiction: str = Form(...),
    domain: str = Form(""),
    question: str = Form(""),
    file: UploadFile = None,
    language: str = Form("en")
):
    summary, articles, cases, sources = await process_legal_research(topic, jurisdiction, domain, question, file, language)
    return templates.TemplateResponse("legal_research.html", {
        "request": request,
        "summary": summary,
        "articles": articles,
        "cases": cases,
        "sources": sources,
        "form_data": {
            "topic": topic, "jurisdiction": jurisdiction,
            "domain": domain, "question": question, "language": language
        }
    })
