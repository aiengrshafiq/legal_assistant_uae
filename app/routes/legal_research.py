# File: app/routes/legal_research.py
from fastapi import APIRouter, Request, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.research_service import process_legal_research

from app.auth.utils import log_query, get_current_user
from fastapi import Depends
from app.auth.models import User

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
    language: str = Form("en"),
    user: User = Depends(get_current_user)
):
    summary, articles, cases, sources = await process_legal_research(topic, jurisdiction, domain, question, file, language)
    
    article_text = "\n".join(articles) if isinstance(articles, list) else str(articles)

    log_query(
        user_email=user.email,
        username=user.username,
        module="Legal Research",
        question=f"Topic: {topic}, Jurisdiction: {jurisdiction}, Domain: {domain}, Question: {question}",
        response=summary + "\n\n" + article_text
    )
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
