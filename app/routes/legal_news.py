
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/legal-news", response_class=HTMLResponse)
async def legal_news_page(request: Request):
    return templates.TemplateResponse("legal_news.html", {"request": request})

@router.get("/api/legal-news")
async def get_legal_news():
    # Sample static data; replace with dynamic data fetching as needed
    news_data = [
        {
            "title": "UAE launches new online platform to clarify all new laws and legislation",
            "summary": "The UAE has launched a new online platform to explain and highlight laws in the country.",
            "url": "https://www.arabianbusiness.com/culture-society/uae-laws-73-new-legal-rulings-in-2023-major-new-website-clarifies-all-legislation-in-english-and-arabic"
        },
        {
            "title": "Overview of Civil Transactions Law and Civil Procedure Law: Key Provisions, Recent Updates",
            "summary": "Understanding UAE’s evolving legal framework: Key insights on civil transactions and procedure laws.",
            "url": "https://thelawreporters.com/overview-of-civil-transactions-law-and-civil-procedure-law-key-provisions-recent-updates"
        },
        {
            "title": "UAE set to use AI to write laws in world first",
            "summary": "The United Arab Emirates is pioneering the use of artificial intelligence to assist in drafting and amending legislation.",
            "url": "https://www.ft.com/content/9019cd51-2b55-4175-81a6-eafcf28609c3"
        }
    ]
    return JSONResponse(content=news_data)
