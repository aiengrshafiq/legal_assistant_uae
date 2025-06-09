from __future__ import annotations
from typing import List, Dict
from app.celery_app import celery_app
from app.services import case_strategy

@celery_app.task(name="case_strategy.process_case_package")
def process_case_package(case_id: str, files: List[Dict[str, bytes]]):
    """
    files  ➜  [{"filename": str, "content": bytes}, …]
    """
    docs        = case_strategy.parse_documents_from_bytes(files)
    classified  = case_strategy.classify_documents(docs)
    timeline    = case_strategy.summarize_timeline(classified)
    status      = case_strategy.infer_status(timeline)
    steps       = case_strategy.recommend_steps(timeline)
    plan        = case_strategy.execution_plan(status, steps)
    case_strategy.store_case_vectors(classified, case_id)

    # the dict is persisted in Redis and fetched by the status route
    return {
        "timeline":   timeline,
        "status":     status,
        "next_steps": steps,
        "plan":       plan,
        "case_id":    case_id,
    }
