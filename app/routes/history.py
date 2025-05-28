from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.auth.database import get_db
from app.auth.utils import get_current_user
from app.auth.models import User
from app.auth.models import QueryLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/history", response_class=HTMLResponse)
async def get_history_page(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = (
        db.query(QueryLog)
        .filter(QueryLog.email == user.email)
        .order_by(QueryLog.timestamp.desc())
        .limit(30)
        .all()
    )
    return templates.TemplateResponse("history.html", {"request": request, "logs": logs})
