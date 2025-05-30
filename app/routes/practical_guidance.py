# === File: app/routes/practical_guidance.py ===

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.guidance_service import generate_guidance

from fastapi import Depends
from app.auth.utils import log_query, get_current_user
from app.auth.models import User


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/api/practical-guidance")
async def practical_guidance(request: Request, user: User = Depends(get_current_user)):
    try:
        data = await request.json()
        guidance = generate_guidance(data)
        log_query(
            user_email=user.email,
            username=user.username,
            module="Practical Guidance",
            question=data.get("legalIssue", ""),
            response=guidance
        )
        return JSONResponse({"guidance": guidance})
    except Exception as e:
        import logging
        logging.exception("Practical guidance error")
        return JSONResponse(status_code=500, content={"error": "Failed to generate practical guidance."})

@router.get("/practical-guidance", response_class=HTMLResponse)
def get_practical_guidance(request: Request):
    return templates.TemplateResponse("practical_guidance.html", {"request": request})