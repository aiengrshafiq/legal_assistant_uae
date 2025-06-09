#!/usr/bin/env sh
set -e

echo "Entrypoint started with ROLE=$ROLE"

if [ "$ROLE" = "worker" ]; then
  echo "Launching Celery worker..."
  exec celery -A app.celery_app worker --concurrency 4 --loglevel INFO
else
  echo "Launching FastAPI app..."
  exec uvicorn app.main:app --host 0.0.0.0 --port 80
fi
