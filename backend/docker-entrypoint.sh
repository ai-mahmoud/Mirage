#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding demo data if needed (seed_demo_data.py is idempotent)..."
python scripts/seed_demo_data.py

exec uvicorn mirage_backend.main:app --host 0.0.0.0 --port 8001
