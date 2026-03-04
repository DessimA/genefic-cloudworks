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

    # 2. Verificar Groq
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        print("  [ERRO] GROQ_API_KEY não encontrada.")
    else:
        print(f"AI (Groq): Configurada")
        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {groq_api_key}"}
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
                models = [m["id"] for m in data.get("data", [])]
                print(f"  [OK] Groq API ativa. Modelos disponíveis: {len(models)}")
                
                target_model = os.environ.get("PRIMARY_MODEL", "llama-3.3-70b-versatile")
                if any(target_model in m for m in models):
                    print(f"  [OK] Modelo '{target_model}' pronto para uso.")
                else:
                    print(f"  [AVISO] Modelo '{target_model}' não encontrado na lista.")
        except Exception as e:
            print(f"  [ERRO] Groq API: Falha na conexão - {e}")

if __name__ == "__main__":
    check_infra()