import json
import os
import time
import logging
import boto3
import base64
import re
from decimal import Decimal
from ollama import Client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuração de endpoints para LocalStack
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL") or f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localstack')}:4566"

dynamodb = boto3.resource("dynamodb", endpoint_url=ENDPOINT_URL)
lambda_client = boto3.client("lambda", endpoint_url=ENDPOINT_URL)

TABLE_NAME = os.environ.get("DYNAMODB_TABLE")
OLLAMA_HOST = os.environ.get("OLLAMA_ENDPOINT", "http://host.docker.internal:11434")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

# Inicializa o Cliente Ollama
ollama_headers = {}
if OLLAMA_API_KEY:
    ollama_headers['Authorization'] = f'Bearer {OLLAMA_API_KEY}'

ollama_client = Client(host=OLLAMA_HOST, headers=ollama_headers)

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
        context = f"DESCRIÇÃO: {repo_info.get('description', 'Sem descrição.')}\n\nDOCUMENTAÇÃO:\n"
        
        if tree and "tree" in tree:
            md_files = [i for i in tree["tree"] if i["path"].lower().endswith(".md")][:3]
            for f in md_files:
                content = fetch_github_content(f"https://api.github.com/repos/{user}/{repo}/contents/{f['path']}?ref={default_branch}")
                if content and "content" in content:
                    text = base64.b64decode(content["content"]).decode('utf-8', errors='ignore')
                    context += f"\n--- {f['path']} ---\n{text}\n"
        return context[:6000]
    except Exception as e:
        logger.error(f"Erro GitHub: {str(e)}")
        return "Erro ao extrair metadados."

def call_ollama_engine(prompt):
    """Chamada para o motor Ollama com lógica de Fallback"""
    models = ["gpt-oss:120b-cloud", "deepseek-v3.1:671b-cloud"]
    last_error = ""

    for model in models:
        try:
            system_instruction = (
                "Você é o 'GENEFIC ATS Optimizer', uma IA especialista em Engenharia de Software e Recrutamento Técnico. "
                "Sua missão é analisar repositórios GitHub e fornecer feedback para melhorar a empregabilidade do desenvolvedor. "
                "Sua saída deve ser EXCLUSIVAMENTE um JSON válido.\n\n"
                "REGRAS DE RESPOSTA:\n"
                "- Responda SEMPRE em Português do Brasil.\n"
                "- Use as chaves: tech_score (number), improvements (lista de strings), ats_summary (string), key_achievements (lista de strings), technologies (lista de strings).\n"
                "- Não inclua explicações fora do JSON."
            )
            
            messages = [
                {'role': 'system', 'content': system_instruction},
                {'role': 'user', 'content': f"Analise este repositório e gere o relatório JSON:\n\n{prompt}"}
            ]

            logger.info(f"Tentando Ollama com modelo: {model} em {OLLAMA_HOST}")
            response = ollama_client.chat(model=model, messages=messages, stream=False)
            
            content = response['message']['content']
            logger.info(f"Sucesso com o modelo {model}")
            return content
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Falha no modelo {model}: {last_error}. Tentando fallback...")
            continue
    
    logger.error(f"Todos os modelos de IA falharam. Último erro: {last_error}")
    raise RuntimeError(f"Falha total na IA após tentar fallback: {last_error}")

def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    if event.get("httpMethod") == "GET":
        params = event.get("queryStringParameters") or {}
        task_id = params.get("task_id")
        if not task_id: return {"statusCode": 400, "headers": CORS_HEADERS, "body": "task_id missing"}
        table = dynamodb.Table(TABLE_NAME)
        item = table.get_item(Key={"user_id": "anonymous", "timestamp": int(task_id)}).get("Item")
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps(item, cls=DecimalEncoder)}

    if event.get("source") == "worker":
        task_id, repo_url = event["task_id"], event["repo_url"]
        try:
            docs = fetch_docs(repo_url)
            analysis = call_ollama_engine(f"Analise: {repo_url}\n{docs}")
            
            match = re.search(r'\{.*\}', analysis, re.DOTALL)
            if not match: raise ValueError("IA não retornou um formato JSON válido.")

            data = json.loads(match.group(0))
            if "error" in data and len(data.keys()) <= 2:
                raise ValueError(f"Ollama retornou erro: {data['error']}")

            required_keys = ["tech_score", "improvements", "ats_summary", "key_achievements", "technologies"]
            for key in required_keys:
                if key not in data:
                    data[key] = [] if key in ["improvements", "key_achievements", "technologies"] else "Informação não disponível"
            
            dynamodb.Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d, tech_score = :ts",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={ ":val": "COMPLETED", ":d": data, ":ts": data.get("tech_score", 0)}
            )
        except Exception as e:
            logger.error(f"Worker process fail: {str(e)}")
            dynamodb.Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={ ":val": "FAILED", ":d": {"error": str(e)}}
            )
        return {}

    try:
        body = json.loads(event.get("body", "{}"))
        repo_url = body.get("repo_url")
        task_id = int(time.time())
        dynamodb.Table(TABLE_NAME).put_item(Item={"user_id": "anonymous", "timestamp": task_id, "status": "PROCESSING", "repo_url": repo_url})
        lambda_client.invoke(FunctionName=context.function_name, InvocationType="Event", Payload=json.dumps({"source": "worker", "task_id": task_id, "repo_url": repo_url}))
        return {"statusCode": 202, "headers": CORS_HEADERS, "body": json.dumps({"task_id": task_id})}
    except Exception as e:
        return {"statusCode": 500, "headers": CORS_HEADERS, "body": json.dumps({"error": str(e)})}