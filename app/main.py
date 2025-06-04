from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.routes import query, draft, summarize, base, auth, legal_news, profile, history,help

from fastapi.middleware.cors import CORSMiddleware
from app.routes import legal_research
from app.routes import practical_guidance,litigation_analysis,document_analysis,case_intelligence, case_strategy


from fastapi.responses import RedirectResponse
from jose import JWTError
from app.auth.utils import decode_token



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(query.router)
app.include_router(draft.router)
app.include_router(summarize.router)
app.include_router(base.router)
app.include_router(legal_research.router)
app.include_router(practical_guidance.router)
app.include_router(litigation_analysis.router)
app.include_router(document_analysis.router)
app.include_router(auth.router)
app.include_router(legal_news.router)
app.include_router(profile.router)
app.include_router(history.router)
app.include_router(help.router)
app.include_router(case_intelligence.router)
app.include_router(case_strategy.router)



@app.middleware("http")
async def enforce_auth(request: Request, call_next):
    if request.url.path.startswith(("/login", "/register", "/static")):
        return await call_next(request)

    token = request.cookies.get("access_token")  # FIXED HERE
    if not token:
        return RedirectResponse("/login")

    try:
        decode_token(token)
    except JWTError:
        return RedirectResponse("/login")

    return await call_next(request)
