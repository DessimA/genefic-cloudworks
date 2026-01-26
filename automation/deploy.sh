#!/bin/bash
set -e

echo "--- Iniciando Processo de Deploy ---"

# 1. Validar o sistema com testes
./automation/tests.sh

# 2. Garantir que o ambiente local esteja pronto (LocalStack)
echo "--- Subindo infraestrutura LocalStack ---"
docker-compose up -d localstack

# Aguarda o LocalStack estar pronto (opcional, mas recomendado)
echo "Aguardando LocalStack iniciar..."
sleep 10

# 3. Executar Terraform para provisionar AWS (via container app)
echo "--- Provisionando Infraestrutura com Terraform ---"
docker-compose run --rm app terraform -chdir=terraform init
docker-compose run --rm app terraform -chdir=terraform apply -auto-approve

echo "--- ⚙️ Configurando endpoint no frontend ---"
API_URL=$(docker-compose run --rm app terraform -chdir=terraform output -raw api_endpoint)
echo "export const CONFIG = { API_ENDPOINT: '$API_URL' };" > frontend/js/config.js

echo "--- Deploy concluído com sucesso! ---"
echo "Infraestrutura pronta no LocalStack."
