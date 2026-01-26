#!/bin/bash
set -e

echo "--- Limpando Ambiente (Docker e AWS/LocalStack) ---"

# Para e remove todos os containers, volumes e imagens órfãs
docker-compose down -v --remove-orphans

# Remove arquivos residuais do Terraform
rm -rf terraform/.terraform
rm -rf terraform/terraform.tfstate*

# Limpa dados persistentes do LocalStack
rm -rf .localstack/

echo "--- Ambiente limpo com sucesso! ---"
