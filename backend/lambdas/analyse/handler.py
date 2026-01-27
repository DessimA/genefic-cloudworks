import json
import os
import logging
import requests
import re
import time
import base64
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configurações via Variáveis de Ambiente
OLLAMA_HOST = os.environ.get("OLLAMA_ENDPOINT", "http://host.docker.internal:11434")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")
PRIMARY_MODEL = "gpt-oss:120b-cloud"
FALLBACK_MODEL = "deepseek-v3.1:671b-cloud"
TABLE_NAME = os.environ.get("DYNAMODB_TABLE")
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL") or f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localstack')}:4566"

# Inicialização de Clientes
# dynamodb = boto3.resource("dynamodb", endpoint_url=ENDPOINT_URL) if 'boto3' in globals() else None
import boto3
dynamodb = boto3.resource("dynamodb", endpoint_url=ENDPOINT_URL)
lambda_client = boto3.client("lambda", endpoint_url=ENDPOINT_URL)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST,GET,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Credentials": "true"
}

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def fetch_github_content(api_url):
    try:
        import urllib.request
        headers = {"User-Agent": "Genefic-Cloudworks-App"}
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))
    except: return None

def fetch_docs(repo_url):
    try:
        parts = repo_url.strip("/").split("/")
        user, repo = parts[-2], parts[-1]
        repo_info = fetch_github_content(f"https://api.github.com/repos/{user}/{repo}")
        if not repo_info: return "Repositório não encontrado."
        
        default_branch = repo_info.get("default_branch", "main")
        tree = fetch_github_content(f"https://api.github.com/repos/{user}/{repo}/git/trees/{default_branch}?recursive=1")
        context = f"DESCRIÇÃO: {repo_info.get('description')}\n\nDOCUMENTAÇÃO:\n"
        
        if tree and "tree" in tree:
            md_files = [i for i in tree["tree"] if i["path"].lower().endswith(".md")][:3]
            for f in md_files:
                content = fetch_github_content(f"https://api.github.com/repos/{user}/{repo}/contents/{f['path']}?ref={default_branch}")
                if content and "content" in content:
                    text = base64.b64decode(content["content"]).decode('utf-8', errors='ignore')
                    context += f"\n--- {f['path']} ---\n{text}\n"
        return context[:6000]
    except Exception as e:
        logger.error(f"Erro GitHub: {e}")
        return "Erro ao extrair metadados."

def call_ollama(prompt):
    models = [PRIMARY_MODEL, FALLBACK_MODEL]
    last_error = ""
    
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    for model in models:
        try:
            logger.info(f"Tentando modelo {model} em {OLLAMA_HOST}")
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system", 
                        "content": "Você é o 'GENEFIC ATS Optimizer', uma IA especialista em Engenharia de Software e Recrutamento Técnico. Analise o repositório GitHub fornecido e gere um relatório de impacto. Retorne APENAS um JSON válido em Português do Brasil com as chaves: tech_score (0-100), improvements (lista), ats_summary (string), key_achievements (lista), technologies (lista)."
                    },
                    {"role": "user", "content": f"Analise este conteúdo de repositório e gere o relatório:\n\n{prompt}"}
                ],
                "stream": False
            }
            resp = requests.post(f"{OLLAMA_HOST}/api/chat", headers=headers, json=payload, timeout=180)
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            
            # Tentar extrair JSON da resposta
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError("Resposta da IA não contém um bloco JSON válido.")
            
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Falha no modelo {model}: {last_error}")
            continue
            
    raise RuntimeError(f"Falha total na IA após tentar fallback. Último erro: {last_error}")

def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    if event.get("httpMethod") == "GET":
        task_id = (event.get("queryStringParameters") or {}).get("task_id")
        if not task_id: return {"statusCode": 400, "headers": CORS_HEADERS, "body": "task_id missing"}
        item = dynamodb.Table(TABLE_NAME).get_item(Key={"user_id": "anonymous", "timestamp": int(task_id)}).get("Item")
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps(item, cls=DecimalEncoder)}

    if event.get("source") == "worker":
        task_id, repo_url = event["task_id"], event["repo_url"]
        try:
            docs = fetch_docs(repo_url)
            data = call_ollama(f"Analise: {repo_url}\n{docs}")
            
            dynamodb.Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d, tech_score = :ts",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":val": "COMPLETED", ":d": data, ":ts": data.get("tech_score", 0)}
            )
        except Exception as e:
            logger.error(f"Worker fail: {e}")
            dynamodb.Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":val": "FAILED", ":d": {"error": str(e)}}
            )
        return {}

    # POST (Início)
    try:
        body = json.loads(event.get("body", "{}"))
        repo_url = body.get("repo_url")
        task_id = int(time.time())
        dynamodb.Table(TABLE_NAME).put_item(Item={"user_id": "anonymous", "timestamp": task_id, "status": "PROCESSING", "repo_url": repo_url})
        lambda_client.invoke(FunctionName=context.function_name, InvocationType="Event", Payload=json.dumps({"source": "worker", "task_id": task_id, "repo_url": repo_url}))
        return {"statusCode": 202, "headers": CORS_HEADERS, "body": json.dumps({"task_id": task_id})}
    except Exception as e:
        return {"statusCode": 500, "headers": CORS_HEADERS, "body": json.dumps({"error": str(e)})}
