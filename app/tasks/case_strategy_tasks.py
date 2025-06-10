from __future__ import annotations
from typing import List, Dict
from app.celery_app import celery_app
from app.services import case_strategy

import os
from azure.storage.blob import BlobServiceClient

# Load Azure Blob connection string from env
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_name = "frontendusercasesdata"

@celery_app.task(name="case_strategy.process_case_package")
def process_case_package(case_id: str, files: List[Dict[str, str]]):
    """
    files ➜ [{"filename": str, "blob_path": str}]
    Downloads each blob, processes content, and returns result.
    """

    decoded_files = []

    for f in files:
        blob_name = f["blob_path"]
        blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
        content = blob_client.download_blob().readall()

        decoded_files.append({
            "filename": f["filename"],
            "content": content
        })

    # Process the decoded files using your case strategy pipeline
    docs        = case_strategy.parse_documents_from_bytes(decoded_files)
    classified  = case_strategy.classify_documents(docs)
    timeline    = case_strategy.summarize_timeline(classified)
    status      = case_strategy.infer_status(timeline)
    steps       = case_strategy.recommend_steps(timeline)
    plan        = case_strategy.execution_plan(status, steps)
    case_strategy.store_case_vectors(classified, case_id)

    return {
        "timeline":   timeline,
        "status":     status,
        "next_steps": steps,
        "plan":       plan,
        "case_id":    case_id,
    }
