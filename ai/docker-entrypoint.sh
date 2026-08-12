#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

exec uvicorn mirage_ai.api:app --host 0.0.0.0 --port 8000
