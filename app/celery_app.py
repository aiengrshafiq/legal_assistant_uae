# app/celery_app.py
import os, ssl, urllib.parse
from celery import Celery

def _maybe_downgrade(url: str | None) -> str | None:
    if not url:
        return url
    # ─── NEW: force-override when we want to use local Redis ───
    if os.getenv("USE_LOCAL_REDIS") == "1":
        return "redis://localhost:6379/0"
    # ─── keep the original auto-downgrade logic ───────────────
    if url.startswith("rediss://"):
        host = urllib.parse.urlparse(url).hostname or ""
        if host in {"localhost", "127.0.0.1", "redis"}:
            return url.replace("rediss://", "redis://", 1)
    return url

broker_url  = _maybe_downgrade(os.getenv("CELERY_BROKER_URL"))
backend_url = _maybe_downgrade(os.getenv("CELERY_RESULT_BACKEND"))

ssl_opts = (
    {"ssl_cert_reqs": ssl.CERT_NONE}
    if broker_url and broker_url.startswith("rediss://")
    else None
)

celery = celery_app = Celery(
    "legalai",
    broker=broker_url,
    backend=backend_url,
    include=["app.tasks.case_strategy_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=100,
    broker_use_ssl=ssl_opts,
    redis_backend_use_ssl=ssl_opts,
)
