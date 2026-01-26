#!/bin/bash
set -e

echo "--- 🚀 Iniciando Deploy Local (Simulação de Produção) ---"

# 1. Garantir que o ambiente local esteja pronto (LocalStack)
echo "--- 📦 Subindo LocalStack ---"
docker-compose up -d localstack

echo "Aguardando LocalStack iniciar (10s)..."
sleep 10

# 2. Provisionar Infraestrutura com Terraform
echo "--- 🏗️ Provisionando Infraestrutura Local ---"
# Extrai as variáveis protegendo contra caracteres especiais
ENV_AI_PROVIDER=$(grep AI_PROVIDER .env | cut -d '=' -f2-)
ENV_GEMINI_KEY=$(grep GEMINI_API_KEY .env | cut -d '=' -f2-)
ENV_DEEPSEEK_KEY=$(grep DEEPSEEK_API_KEY .env | cut -d '=' -f2-)

docker-compose run --rm app terraform -chdir=terraform init
docker-compose run --rm app terraform -chdir=terraform apply -auto-approve \
  -var="enable_cloudfront=false" \
  -var="ai_provider=$ENV_AI_PROVIDER" \
  -var="gemini_api_key=$ENV_GEMINI_KEY" \
  -var="deepseek_api_key=$ENV_DEEPSEEK_KEY"

# 3. Obter o nome do bucket criado
echo "--- 🔍 Obtendo informações do bucket ---"
BUCKET_NAME=$(docker-compose run --rm app terraform -chdir=terraform output -raw s3_bucket_name)

# 4. Injetar Endpoint no Frontend
echo "--- ⚙️ Configurando endpoint no frontend ---"
API_ID=$(docker-compose run --rm app terraform -chdir=terraform output -raw api_id)
# Formato exato para LocalStack rest-apis
API_URL="http://localhost:4566/restapis/$API_ID/dev/_user_request_/upload"
echo "export const CONFIG = { API_ENDPOINT: '$API_URL' };" > frontend/js/config.js

# 5. Upload do Frontend para o S3
echo "--- ⬆️ Uploading Frontend para S3 (LocalStack) ---"
docker-compose run --rm app python src/utils/upload_frontend.py "$BUCKET_NAME"

echo "--- ✅ Deploy Local Concluído! ---"
echo "URL de Acesso (S3 Website): http://$BUCKET_NAME.s3-website.localhost.localstack.cloud:4566"
echo "Nota: Certifique-se de que o LocalStack está mapeado corretamente no seu host."
