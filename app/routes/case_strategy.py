# =============================
# 📦 app/routes/case_strategy.py
# =============================
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from celery.result import AsyncResult

from app.tasks.case_strategy_tasks import process_case_package
from app.qachain import ask_question_in_case      # unchanged

router    = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ─────────────────────────────────────────────────────────── UI start page
@router.get("/case-strategy", response_class=HTMLResponse)
async def form(request: Request):
    return templates.TemplateResponse("case_strategy.html", {"request": request})

# ─────────────────────────────────────────────────────────── fire-and-forget
@router.post("/case-strategy/process", response_class=JSONResponse, status_code=202)
async def process_case(files: list[UploadFile] = File(...)):
    case_id = f"case_{uuid4().hex}"

    # read uploads into memory once; Celery serialises the dict
    payload = [{
        "filename": f.filename,
        "content":  await f.read()
    } for f in files]

    task = process_case_package.delay(case_id, payload)   # → Redis queue
    return {"case_id": case_id, "task_id": task.id}

# ─────────────────────────────────────────────────────────── poll endpoint
@router.get("/case-strategy/result/{task_id}", response_class=JSONResponse)
async def get_result(task_id: str):
    task = AsyncResult(task_id)
    if task.successful():
        return task.result
    return {"state": task.state}          # PENDING / STARTED / RETRY / FAILURE

# ─────────────────────────────────────────────────────────── QA unchanged
@router.post("/case-strategy/ask", response_class=JSONResponse)
async def case_qa(case_id: str = Form(...), question: str = Form(...)):
    try:
        answer = ask_question_in_case(case_id, question)
        return {"answer": answer}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/case-strategy/result-page.html", response_class=HTMLResponse)
async def result_page(request: Request):
    """
    Renders the final results view.  Data are injected on the client side
    from sessionStorage (see JavaScript in case_strategy.html).
    """
    return templates.TemplateResponse("result-page.html", {"request": request})