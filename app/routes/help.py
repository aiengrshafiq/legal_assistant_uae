from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/help", response_class=HTMLResponse)
async def get_help_page(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})
