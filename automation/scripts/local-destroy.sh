#!/usr/bin/env bash
set -euo pipefail

# Prevenir conversão de caminhos no Git Bash do Windows
export MSYS_NO_PATHCONV=1

PROJECT_ROOT=$(pwd)

echo "🗑️ Destruindo infraestrutura Terraform..."
docker run --rm \
  --network genefic-net \
  -v "$PROJECT_ROOT:/app" \
  -w /app/infrastructure/terraform \
  -e AWS_ACCESS_KEY_ID=test \
  -e AWS_SECRET_ACCESS_KEY=test \
  -e AWS_DEFAULT_REGION=us-east-1 \
  hashicorp/terraform:latest destroy -auto-approve || echo "⚠️ Terraform destroy falhou ou recursos não existem."

echo "🛑 Parando containers LocalStack e Ollama..."
docker-compose -f infrastructure/local/docker-compose.yml down -v --remove-orphans

echo "✅ Ambiente local limpo com sucesso."
