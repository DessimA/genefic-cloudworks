#!/bin/bash
set -e

echo "--- Iniciando Testes do Sistema ---"

# Executa os testes usando o container de testes definido no docker-compose
docker-compose run --rm tests

echo "--- Testes concluídos com sucesso! ---"
