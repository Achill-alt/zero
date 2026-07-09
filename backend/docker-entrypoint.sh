#!/bin/bash
set -e

echo "[docker-entrypoint] Seeding database (idempotent)..."
python seed.py

echo "[docker-entrypoint] Starting uvicorn on port 8000..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
