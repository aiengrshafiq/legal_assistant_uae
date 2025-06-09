#!/usr/bin/env sh
set -e

if [ "$ROLE" = "worker" ]; then
  # Celery worker (production uses prefork; Windows dev can use --pool=solo)
  exec celery -A app.celery_app worker --concurrency 4 --loglevel INFO
else
  # FastAPI web
  exec uvicorn app.main:app --host 0.0.0.0 --port 80
fi
