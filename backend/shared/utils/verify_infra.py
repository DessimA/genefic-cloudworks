import boto3
import os
import urllib.request
import json

def check_infra():
    endpoint = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")
    ollama_endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://host.docker.internal:11434/api/tags")
    
    print(f"--- 🔍 Verificando Infraestrutura ---")
    
    # 1. Verificar LocalStack (S3 e DynamoDB)
    print(f"AWS (LocalStack): {endpoint}")
    try:
        s3 = boto3.client("s3", endpoint_url=endpoint, region_name="us-east-1")
        ddb = boto3.client("dynamodb", endpoint_url=endpoint, region_name="us-east-1")
        
        buckets = s3.list_buckets()["Buckets"]
        print(f"  [OK] S3 Buckets: {[b['Name'] for b in buckets]}")
        
        tables = ddb.list_tables()["TableNames"]
        print(f"  [OK] DynamoDB Tables: {tables}")
    except Exception as e:
        print(f"  [ERRO] AWS: {e}")

    # 2. Verificar Ollama
    print(f"AI (Ollama): {ollama_endpoint}")
    try:
        with urllib.request.urlopen(ollama_endpoint, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            print(f"  [OK] Ollama API ativa. Modelos disponíveis: {models}")
            
            target_model = os.environ.get("OLLAMA_MODEL", "llama3.2")
            if any(target_model in m for m in models):
                print(f"  [OK] Modelo '{target_model}' pronto para uso.")
            else:
                print(f"  [AVISO] Modelo '{target_model}' não encontrado na lista.")
    except Exception as e:
        print(f"  [ERRO] Ollama: Não respondendo. Certifique-se de que o container está rodando e a porta 11434 está aberta.")

if __name__ == "__main__":
    check_infra()