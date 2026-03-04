import json
import os
import time
import logging
import boto3
import base64
import re
import urllib.request
import urllib.error
from decimal import Decimal
from groq import Groq

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configurações globais
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL") or f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localstack')}:4566"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
TABLE_NAME = os.environ.get("DYNAMODB_TABLE")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Modelos obrigatórios
PRIMARY_MODEL = os.environ.get("PRIMARY_MODEL")
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST,GET,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Credentials": "true"
}

# Clientes preguiçosos
_dynamodb = None
_lambda_client = None
_groq_client = None

def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", endpoint_url=ENDPOINT_URL)
    return _dynamodb

def get_lambda_client():
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda", endpoint_url=ENDPOINT_URL)
    return _lambda_client

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY:
            logger.error("❌ ERRO CRÍTICO: GROQ_API_KEY não configurada.")
            raise RuntimeError("Chave de API Groq ausente.")
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

class GitHubRateLimitError(Exception):
    pass

def fetch_github_content(api_url, retry_count=0, max_retries=2):
    headers = {
        "User-Agent": "Genefic-Cloudworks-MVP/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            body = e.read().decode('utf-8').lower()
            if 'rate limit' in body:
                raise GitHubRateLimitError("GitHub Rate Limit atingido")
        if e.code in [502, 503, 504] and retry_count < max_retries:
            time.sleep((retry_count + 1) * 2)
            return fetch_github_content(api_url, retry_count + 1, max_retries)
        raise Exception(f"GitHub API falhou: HTTP {e.code}")
    except Exception as e:
        raise Exception(f"Erro inesperado: {str(e)}")

def fetch_docs(repo_url):
    """Extrai contexto profundo do repositório para análise de alta qualidade."""
    try:
        parts = repo_url.strip("/").split("/")
        user, repo = parts[-2], parts[-1]
        
        repo_info = fetch_github_content(f"https://api.github.com/repos/{user}/{repo}")
        default_branch = repo_info.get("default_branch", "main")
        
        # Buscar árvore completa
        tree_res = fetch_github_content(f"https://api.github.com/repos/{user}/{repo}/git/trees/{default_branch}?recursive=1")
        files = tree_res.get("tree", [])
        
        # 1. Mapear estrutura de diretórios (máx 100 arquivos)
        structure = [f["path"] for f in files if f["type"] == "blob"][:100]
        
        context_parts = [
            f"=== METADADOS ===",
            f"Repositório: {user}/{repo}",
            f"Descrição: {repo_info.get('description')}",
            f"Estrutura de Arquivos (Amostra): {', '.join(structure)}",
            f"\n=== CONTEÚDO TÉCNICO ==="
        ]
        
        # Prioridades de extração (Expandido para Java/Spring e outros)
        priority_patterns = [
            r"readme\.md$", 
            r"package\.json$", 
            r"requirements\.txt$", 
            r"pom\.xml$", 
            r"build\.gradle$",
            r"docker-compose\.yml$", 
            r"Dockerfile$",
            r"application\.properties$",
            r"application\.yml$"
        ]
        
        found_files = 0
        for f in files:
            if found_files >= 8: break # Aumentado para 8 arquivos
            path = f["path"]
            if any(re.search(p, path, re.I) for p in priority_patterns):
                try:
                    content_data = fetch_github_content(f"https://api.github.com/repos/{user}/{repo}/contents/{path}?ref={default_branch}")
                    if "content" in content_data:
                        text = base64.b64decode(content_data["content"]).decode('utf-8', errors='ignore')
                        # Pegar mais conteúdo do README, menos de arquivos de configuração
                        limit = 4000 if "readme" in path.lower() else 1500
                        context_parts.append(f"\n--- ARQUIVO: {path} ---\n{text[:limit]}")
                        found_files += 1
                except: continue
        
        return "\n".join(context_parts)
    except Exception as e:
        return f"Erro ao extrair metadados: {str(e)}"

def call_groq_engine(prompt):
    client = get_groq_client()
    system_prompt = """Você é o 'GENEFIC AUDITOR', um arquiteto de software sênior especializado em Auditoria Técnica e ATS.

SUA TAREFA:
Realizar uma análise CRÍTICA e PRECISA do repositório fornecido.

REGRAS DE OURO (NÃO NEGOCIÁVEIS):
1. AUDITORIA REAL: Antes de sugerir uma melhoria, verifique se ela já não existe no código ou README.
2. PROIBIDO GENERICISMOS: Não diga "melhorar performance" ou "limpar código". Diga EXATAMENTE o que e onde.
3. TECH SCORE HONESTO: Use a escala abaixo:
   - 0-40: CRUD básico, sem testes, sem Docker, sem CI/CD.
   - 41-70: Projeto estruturado, com Docker e documentação razoável.
   - 71-90: Arquitetura robusta (Hexagonal/Clean), Testes Unitários/Integrados, Redis/Cache, Segurança (JWT/OAuth2), Documentação impecável.
   - 91-100: Excelência técnica, Cloud Native, Observabilidade, Alta Escala, Cobertura de testes > 90%.
4. CONQUISTAS: Cite tecnologias específicas encontradas nos arquivos de dependência (pom.xml, package.json).
5. FORMATO: Retorne APENAS o JSON abaixo, sem markdown.

ESTRUTURA:
{
  "tech_score": num,
  "technologies": ["Lista precisa de libs e frameworks detectados"],
  "key_achievements": ["Conquista técnica comprovada por arquivo X ou trecho Y"],
  "improvements": ["Melhoria que REALMENTE falta. Se o projeto já tem Redis, NÃO sugira Redis."],
  "ats_summary": "Resumo profissional denso, focado em cargos Senior/Staff. Evite adjetivos, use fatos."
}

RESTRIÇÃO ADICIONAL:
- Se encontrar Spring Boot e Redis, foque em conquistas de resiliência e performance.
- Se o README cita uma feature, considere-a como 'Implementada' e analise a qualidade da implementação."""

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        if not model: continue
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"ANALISE O REPOSITÓRIO ABAIXO:\n\n{prompt}"}
                ],
                temperature=0.1, # Baixa temperatura para precisão
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Falha no modelo {model}: {e}")
            continue
    raise RuntimeError("Falha total na IA.")

def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    if event.get("httpMethod") == "GET":
        task_id = (event.get("queryStringParameters") or {}).get("task_id")
        if not task_id: return {"statusCode": 400, "headers": CORS_HEADERS, "body": json.dumps({"error": "task_id ausente"})}
        table = get_dynamodb().Table(TABLE_NAME)
        item = table.get_item(Key={"user_id": "anonymous", "timestamp": int(task_id)}).get("Item")
        if not item: return {"statusCode": 404, "headers": CORS_HEADERS, "body": json.dumps({"error": "Task não encontrada"})}
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps(item, cls=DecimalEncoder)}

    if event.get("source") == "worker":
        task_id, repo_url = event["task_id"], event["repo_url"]
        try:
            docs = fetch_docs(repo_url)
            raw_analysis = call_groq_engine(docs)
            
            # Limpeza rigorosa de markdown
            clean_json = re.sub(r'```json|```', '', raw_analysis).strip()
            try:
                data = json.loads(clean_json)
            except:
                match = re.search(r'\{.*\}', clean_json, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"tech_score": 50, "ats_summary": "Erro no parsing"}

            # Validação de sugestões redundantes (Filtro extra no backend)
            techs_found = [t.lower() for t in data.get("technologies", [])]
            data["improvements"] = [imp for i, imp in enumerate(data.get("improvements", [])) 
                                   if not any(t in imp.lower() for t in techs_found)][:3]
            
            if not data["improvements"]:
                data["improvements"] = ["Refinar cobertura de testes de integração", "Implementar métricas de observabilidade (Micrometer/Prometheus)"]

            get_dynamodb().Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d, tech_score = :ts",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":val": "COMPLETED", ":d": data, ":ts": data.get("tech_score", 0)}
            )
        except Exception as e:
            logger.error(f"Erro no worker: {e}")
            get_dynamodb().Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":val": "FAILED", ":d": {"error": str(e)}}
            )
        return {}

    try:
        body = json.loads(event.get("body", "{}"))
        repo_url = body.get("repo_url")
        if not repo_url: return {"statusCode": 400, "headers": CORS_HEADERS, "body": json.dumps({"error": "repo_url obrigatório"})}
        
        task_id = int(time.time())
        get_dynamodb().Table(TABLE_NAME).put_item(
            Item={"user_id": "anonymous", "timestamp": task_id, "status": "PROCESSING", "repo_url": repo_url}
        )
        
        get_lambda_client().invoke(
            FunctionName=context.function_name,
            InvocationType="Event",
            Payload=json.dumps({"source": "worker", "task_id": task_id, "repo_url": repo_url})
        )
        return {"statusCode": 202, "headers": CORS_HEADERS, "body": json.dumps({"task_id": task_id})}
    except Exception as e:
        return {"statusCode": 500, "headers": CORS_HEADERS, "body": json.dumps({"error": str(e)})}
