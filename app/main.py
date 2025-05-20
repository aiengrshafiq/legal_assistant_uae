from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.routes import query, draft, summarize, base

from fastapi.middleware.cors import CORSMiddleware
from app.routes import legal_research
from app.routes import practical_guidance,litigation_analysis,document_analysis



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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
