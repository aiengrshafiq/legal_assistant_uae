# ✅ routes/practical_guidance.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.guidance_service import generate_guidance


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/api/practical-guidance")
async def practical_guidance(request: Request):
    data = await request.json()
    prompt = generate_guidance(data)
    return JSONResponse({"guidance": prompt})

@router.get("/practical-guidance", response_class=HTMLResponse)
async def get_legal_research(request: Request):
    return templates.TemplateResponse("practical_guidance.html", {"request": request})