#!/bin/bash
set -e

echo "========================================"
echo "    Finance Inbox Backend (Supabase)"
echo "========================================"

# Load environment variables if .env exists
if [ -f .env ]; then
  echo "[INFO] Loading environment variables from .env"
  export $(grep -v '^#' .env | xargs)
fi

echo "[INFO] Starting FastAPI server..."
uvicorn main:app --reload --host 0.0.0.0 --port ${PORT:-8000}

