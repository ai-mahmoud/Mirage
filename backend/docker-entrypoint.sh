#!/bin/sh
set -e

DB_URL="${BACKEND_DATABASE_URL:-sqlite:///./backend.db}"
DB_PATH="${DB_URL#sqlite:///}"

mkdir -p "$(dirname "$DB_PATH")" 2>/dev/null || true

if [ ! -f "$DB_PATH" ]; then
  echo "No existing database at $DB_PATH — seeding realistic demo data..."
  python scripts/seed_demo_data.py
fi

exec uvicorn mirage_backend.main:app --host 0.0.0.0 --port 8001
