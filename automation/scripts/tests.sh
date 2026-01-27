#!/bin/bash
set -e

PROJECT_ROOT=$(pwd)

echo "🧪 Running Tests..."

docker run --rm \
  -v "$PROJECT_ROOT:/app" \
  -w /app \
  -e PYTHONPATH=/app/backend \
  python:3.11-slim \
  bash -c "pip install --upgrade pip && \
           pip install -r requirements.txt pytest pytest-mock && \
           pytest backend/tests/"

echo "✅ Tests passed!"
