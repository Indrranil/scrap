#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding initial data..."
python scripts/seed_data.py

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${API_PORT:-8000}"
