from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from sqlalchemy.orm import Session

from app.auth.database import get_db
from app.auth.models import User
from app.auth.utils import verify_password, hash_password, create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse("/login?error=true", status_code=HTTP_302_FOUND)
    
    token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/", status_code=HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == email).first():
        return RedirectResponse("/register?error=exists", status_code=HTTP_302_FOUND)
    
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password)
    )
    db.add(user)
    db.commit()
    return RedirectResponse("/login", status_code=HTTP_302_FOUND)
