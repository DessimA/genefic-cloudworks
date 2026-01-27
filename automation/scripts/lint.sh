#!/bin/bash
set -e

PROJECT_ROOT=$(pwd)

echo "🔍 Running Linting..."

# Python Linting
docker run --rm \
  -v "$PROJECT_ROOT:/app" \
  -w /app \
  python:3.11-slim \
  bash -c "pip install --upgrade pip && \
           pip install flake8 black isort && \
           flake8 backend/ --exclude=backend/lambdas/dist && \
           black --check backend/ && \
           isort --check-only backend/"

# Terraform Linting
docker run --rm \
  -v "$PROJECT_ROOT/infrastructure/terraform:/workspace" \
  -w /workspace \
  hashicorp/terraform:latest fmt -check

echo "✅ Linting passed!"
