#!/bin/bash
set -e

# Prevenir conversão de caminhos no Git Bash do Windows
export MSYS_NO_PATHCONV=1

# Configurações de Diretórios
PROJECT_ROOT=$(pwd)
INFRA_DIR="$PROJECT_ROOT/infrastructure/local"
TF_DIR="$PROJECT_ROOT/infrastructure/terraform"
FRONTEND_DIR="$PROJECT_ROOT/frontend/public"

# Carregar variaveis de ambiente (.env)
if [ -f "$PROJECT_ROOT/.env" ]; then
  echo "📄 Carregando variáveis do .env..."
  set -a 
  source "$PROJECT_ROOT/.env"
  set +a
else
  echo "❌ Erro: Arquivo .env não encontrado em $PROJECT_ROOT"
  exit 1
fi

echo "🧹 Limpando ambiente anterior..."
docker-compose -p genefic -f infrastructure/local/docker-compose.yml down --remove-orphans 2>/dev/null || true
docker rm -f genefic-localstack genefic-dynamodb-admin 2>/dev/null || true

echo "🚀 Iniciando ambiente local..."
docker-compose -p genefic --env-file .env -f infrastructure/local/docker-compose.yml up -d

echo "⏳ Aguardando LocalStack ficar pronto em localhost:4566..."
until curl -s http://localhost:4566/_localstack/health | grep -q "\"services\":"; do
  sleep 2
  echo -n "."
done
echo -e "\n✅ LocalStack está pronto!"

echo "📦 Preparando pacote da Lambda de Análise..."
UPLOAD_LAMBDA_SRC="backend/lambdas/analyse/handler.py"
UPLOAD_LAMBDA_DIST="backend/lambdas/dist"
mkdir -p "$PROJECT_ROOT/$UPLOAD_LAMBDA_DIST"
rm -rf "$PROJECT_ROOT/$UPLOAD_LAMBDA_DIST/*"

# Instala dependências e copia o handler
docker run --rm \
  -v "$PROJECT_ROOT:/app" \
  -w /app \
  python:3.11-slim \
  bash -c "pip install --upgrade pip && \
           pip install --no-cache-dir -r requirements.txt -t $UPLOAD_LAMBDA_DIST && \
           cp $UPLOAD_LAMBDA_SRC $UPLOAD_LAMBDA_DIST/handler.py"

echo "🛠️ Aplicando infraestrutura via Terraform..."
docker run --rm \
  --network genefic-net \
  -v "$PROJECT_ROOT:/app" \
  -w /app/infrastructure/terraform \
  -e TF_VAR_environment="local" \
  -e TF_VAR_ollama_endpoint="http://host.docker.internal:11434" \
  -e TF_VAR_ollama_model="${OLLAMA_MODEL:-llama3.2}" \
  -e TF_VAR_ollama_api_key="${OLLAMA_API_KEY}" \
  -e AWS_ACCESS_KEY_ID="test" \
  -e AWS_SECRET_ACCESS_KEY="test" \
  -e AWS_DEFAULT_REGION="us-east-1" \
  hashicorp/terraform:latest init -upgrade

docker run --rm \
  --network genefic-net \
  -v "$PROJECT_ROOT:/app" \
  -w /app/infrastructure/terraform \
  -e TF_VAR_environment="local" \
  -e TF_VAR_ollama_endpoint="http://host.docker.internal:11434" \
  -e TF_VAR_ollama_model="${OLLAMA_MODEL:-llama3.2}" \
  -e TF_VAR_ollama_api_key="${OLLAMA_API_KEY}" \
  -e AWS_ACCESS_KEY_ID="test" \
  -e AWS_SECRET_ACCESS_KEY="test" \
  -e AWS_DEFAULT_REGION="us-east-1" \
  hashicorp/terraform:latest apply -auto-approve

echo "📍 Obtendo informações da infraestrutura..."
API_ID=$(docker run --rm -v "$PROJECT_ROOT:/app" -w /app/infrastructure/terraform hashicorp/terraform:latest output -raw api_id)
S3_BUCKET_NAME=$(docker run --rm -v "$PROJECT_ROOT:/app" -w /app/infrastructure/terraform hashicorp/terraform:latest output -raw s3_bucket_name)

# Formato padrão para LocalStack
REAL_API_URL="http://localhost:4566/_aws/execute-api/$API_ID/local/upload"

echo "export const CONFIG = { API_ENDPOINT: '$REAL_API_URL' };" > "$FRONTEND_DIR/js/config.js"
echo "✅ Config.js atualizado com: $REAL_API_URL"

echo "🌐 Sincronizando Frontend com S3..."
echo "   Bucket Alvo: $S3_BUCKET_NAME"

docker run --rm \
  --network genefic-net \
  -v "$FRONTEND_DIR:/frontend" \
  -e AWS_ACCESS_KEY_ID="test" \
  -e AWS_SECRET_ACCESS_KEY="test" \
  -e AWS_DEFAULT_REGION="us-east-1" \
  amazon/aws-cli:latest --endpoint-url=http://genefic-localstack:4566 s3 sync /frontend s3://$S3_BUCKET_NAME/ --acl public-read

echo "✨ Deploy local concluído com sucesso!"
echo "-------------------------------------------------------"
echo "🌐 Dashboard URL: http://$S3_BUCKET_NAME.s3-website.localhost.localstack.cloud:4566"
echo "📊 DynamoDB Admin: http://localhost:8001"
echo "📍 LocalStack API: http://localhost:4566"
echo "-------------------------------------------------------"