from fastapi import APIRouter, UploadFile, Form, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.utils import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/coming-soon", response_class=HTMLResponse)
async def coming_soon(request: Request):
    return templates.TemplateResponse("coming_soon.html", {"request": request})

@router.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


