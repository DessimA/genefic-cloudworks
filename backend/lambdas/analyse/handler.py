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
from ollama import Client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configurações
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL") or f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localstack')}:4566"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
TABLE_NAME = os.environ.get("DYNAMODB_TABLE")
OLLAMA_HOST = os.environ.get("OLLAMA_ENDPOINT", "http://host.docker.internal:11434")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

# Modelos obrigatórios via ambiente (sem defaults por segurança/manutenção)
PRIMARY_MODEL = os.environ.get("PRIMARY_MODEL")
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL")

if not PRIMARY_MODEL or not FALLBACK_MODEL:
    logger.error("❌ ERRO CRÍTICO: PRIMARY_MODEL ou FALLBACK_MODEL não configurados nas variáveis de ambiente.")
    raise RuntimeError("Configuração de IA ausente.")

# Inicialização de Clientes
dynamodb = boto3.resource("dynamodb", endpoint_url=ENDPOINT_URL)
lambda_client = boto3.client("lambda", endpoint_url=ENDPOINT_URL)

ollama_headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}
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

class GitHubRateLimitError(Exception):
    """Exceção lançada quando GitHub rate limit é atingido"""
    pass

def fetch_github_content(api_url, retry_count=0, max_retries=2):
    """
    Faz requisição à GitHub API com autenticação e retry logic.
    """
    # Configurar headers com autenticação
    headers = {
        "User-Agent": "Genefic-Cloudworks-MVP/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # ✅ ADICIONAR TOKEN SE DISPONÍVEL
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        logger.info("✅ Usando GitHub Token autenticado")
    else:
        logger.warning("⚠️ GitHub Token NÃO configurado - Rate limit: 60 req/hora")
    
    try:
        req = urllib.request.Request(api_url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=20) as response:
            # ✅ LOGAR RATE LIMIT RESTANTE
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
            rate_limit_reset = response.headers.get('X-RateLimit-Reset')
            
            if rate_limit_remaining:
                logger.info(f"📊 Rate Limit Restante: {rate_limit_remaining}")
                
                # ✅ ALERTA SE ESTIVER ACABANDO
                if int(rate_limit_remaining) < 10:
                    reset_time = time.strftime('%H:%M:%S', time.localtime(int(rate_limit_reset)))
                    logger.warning(f"⚠️ Rate Limit Baixo! Reseta às {reset_time}")
            
            return json.loads(response.read().decode("utf-8"))
            
    except urllib.error.HTTPError as e:
        # ✅ TRATAMENTO ESPECÍFICO DE RATE LIMIT
        if e.code == 403:
            error_body = e.read().decode('utf-8')
            
            # Verificar se é rate limit
            if 'rate limit exceeded' in error_body.lower():
                reset_time = e.headers.get('X-RateLimit-Reset')
                if reset_time:
                    reset_str = time.strftime('%H:%M:%S', time.localtime(int(reset_time)))
                    error_msg = f"GitHub Rate Limit atingido. Reseta às {reset_str}"
                else:
                    error_msg = "GitHub Rate Limit atingido"
                
                logger.error(f"❌ {error_msg}")
                raise GitHubRateLimitError(error_msg)
        
        # ✅ RETRY PARA ERROS TEMPORÁRIOS (502, 503)
        if e.code in [502, 503, 504] and retry_count < max_retries:
            wait_time = (retry_count + 1) * 2  # Backoff exponencial: 2s, 4s, 6s
            logger.warning(f"⚠️ Erro {e.code}, tentando novamente em {wait_time}s...")
            time.sleep(wait_time)
            return fetch_github_content(api_url, retry_count + 1, max_retries)
        
        logger.error(f"❌ GitHub API Error {e.code}")
        raise Exception(f"GitHub API falhou: HTTP {e.code}")
        
    except urllib.error.URLError as e:
        logger.error(f"❌ Erro de Rede: {str(e)}")
        raise Exception(f"Falha na conexão com GitHub: {str(e)}")
    
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}")
        raise

def fetch_docs(repo_url):
    """
    Extrai metadados completos do repositório GitHub para análise robusta.
    """
    try:
        # Extrair owner e repo da URL
        parts = repo_url.strip("/").split("/")
        user, repo = parts[-2], parts[-1]
        
        logger.info(f"🔍 Analisando repositório: {user}/{repo}")
        
        # 1. BUSCAR INFORMAÇÕES BÁSICAS DO REPO
        repo_info = fetch_github_content(f"https://api.github.com/repos/{user}/{repo}")
        if not repo_info:
            return "❌ Repositório não encontrado ou inacessível."
        
        # Extrair metadados básicos
        description = repo_info.get('description', 'Sem descrição')
        language = repo_info.get('language', 'Não especificado')
        stars = repo_info.get('stargazers_count', 0)
        forks = repo_info.get('forks_count', 0)
        has_wiki = repo_info.get('has_wiki', False)
        has_issues = repo_info.get('has_issues', False)
        topics = repo_info.get('topics', [])
        default_branch = repo_info.get("default_branch", "main")
        
        logger.info(f"📋 Linguagem Principal: {language} | ⭐ Stars: {stars} | 🍴 Forks: {forks}")
        
        # 2. BUSCAR ÁRVORE DE ARQUIVOS (estrutura do repo)
        tree_url = f"https://api.github.com/repos/{user}/{repo}/git/trees/{default_branch}?recursive=1"
        tree = fetch_github_content(tree_url)
        
        if not tree or "tree" not in tree:
            return f"DESCRIÇÃO: {description}\n\nERRO: Não foi possível acessar arquivos do repositório."
        
        all_files = tree["tree"]
        file_paths = [f["path"] for f in all_files if f["type"] == "blob"]
        
        logger.info(f"📂 Total de arquivos encontrados: {len(file_paths)}")
        
        # 3. ANÁLISE DE ESTRUTURA DE PASTAS
        has_src = any("src/" in p for p in file_paths)
        has_tests = any(p.lower().startswith(("test", "tests/", "__test")) for p in file_paths)
        has_docs = any("docs/" in p for p in file_paths)
        has_ci = any(".github/workflows" in p or ".gitlab-ci" in p or "jenkinsfile" in p.lower() for p in file_paths)
        has_docker = any("dockerfile" in p.lower() for p in file_paths)
        
        # 4. IDENTIFICAR ARQUIVOS-CHAVE PARA EXTRAÇÃO
        priority_files = []
        
        # README principal (prioridade máxima)
        readme_candidates = [p for p in file_paths if p.lower() in ["readme.md", "readme.txt", "readme.rst"]]
        if readme_candidates:
            priority_files.append(("README", readme_candidates[0]))
        
        # Arquivos de dependências
        dep_patterns = {
            "package.json": "npm/Node.js",
            "requirements.txt": "pip/Python",
            "Pipfile": "pipenv/Python",
            "go.mod": "Go Modules",
            "Cargo.toml": "Cargo/Rust",
            "composer.json": "Composer/PHP",
            "pom.xml": "Maven/Java",
            "build.gradle": "Gradle/Java"
        }
        
        for dep_file, tech in dep_patterns.items():
            matches = [p for p in file_paths if dep_file in p.lower()]
            if matches:
                priority_files.append((f"DEPENDENCIES_{tech}", matches[0]))
                logger.info(f"✅ Encontrado: {dep_file} ({tech})")
        
        # Arquivos de configuração relevantes
        config_files = [
            "Dockerfile",
            ".github/workflows/",
            ".gitlab-ci.yml",
            "docker-compose.yml",
            "terraform.tf"
        ]
        
        for config in config_files:
            matches = [p for p in file_paths if config.lower() in p.lower()]
            if matches:
                priority_files.append((f"CONFIG_{config.replace('/', '_')}", matches[0]))
        
        # Documentação adicional (limitado a 2 arquivos)
        other_docs = [p for p in file_paths if p.lower().endswith(".md") and p.lower() not in ["readme.md", "contributing.md"]][:2]
        for doc in other_docs:
            priority_files.append(("DOC", doc))
        
        # 5. EXTRAIR CONTEÚDO DOS ARQUIVOS PRIORITÁRIOS
        context_parts = []
        
        # Cabeçalho com metadados
        context_parts.append(f"""
=== METADADOS DO REPOSITÓRIO ===
Nome: {user}/{repo}
Descrição: {description}
Linguagem Principal: {language}
Engajamento: {stars} stars, {forks} forks
Topics/Tags: {', '.join(topics) if topics else 'Nenhum'}
Wiki: {'Sim' if has_wiki else 'Não'}
Issues Abertas: {'Sim' if has_issues else 'Não'}

=== ANÁLISE DE ESTRUTURA ===
✅ Pasta src/: {'SIM' if has_src else 'NÃO'}
✅ Testes: {'SIM' if has_tests else 'NÃO'}
✅ Documentação (docs/): {'SIM' if has_docs else 'NÃO'}
✅ CI/CD: {'SIM' if has_ci else 'NÃO'}
✅ Docker: {'SIM' if has_docker else 'NÃO'}

=== ARQUIVOS ANALISADOS ===
""")
        
        total_chars = len(context_parts[0])
        max_chars = 8000  # Limite inteligente (deixa espaço para o prompt)
        
        for label, file_path in priority_files:
            if total_chars >= max_chars:
                context_parts.append("\n[... Contexto truncado por limite de tamanho ...]\n")
                break
            
            try:
                content_data = fetch_github_content(
                    f"https://api.github.com/repos/{user}/{repo}/contents/{file_path}?ref={default_branch}"
                )
                
                if content_data and "content" in content_data:
                    decoded_content = base64.b64decode(content_data["content"]).decode('utf-8', errors='ignore')
                    
                    # Limitar tamanho de cada arquivo
                    file_limit = 2000 if label.startswith("README") else 1000
                    truncated_content = decoded_content[:file_limit]
                    if len(decoded_content) > file_limit:
                        truncated_content += "\n[... arquivo truncado ...]"
                    
                    context_parts.append(f"\n--- [{label}] {file_path} ---\n{truncated_content}\n")
                    total_chars += len(context_parts[-1])
                    
                    logger.info(f"📄 Extraído: {file_path} ({len(truncated_content)} chars)")
                    
            except Exception as e:
                logger.warning(f"⚠️ Falha ao extrair {file_path}: {str(e)}")
                continue
        
        final_context = "".join(context_parts)
        logger.info(f"✅ Contexto final montado: {len(final_context)} caracteres")
        
        return final_context
        
    except GitHubRateLimitError:
        # Re-lançar erro de rate limit para tratamento na camada superior
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao extrair metadados do repositório: {str(e)}")
        return f"ERRO CRÍTICO: {str(e)}"

def call_ollama_engine(prompt):
    """
    Chama Ollama com prompt otimizado e validação de qualidade.
    """
    models = [PRIMARY_MODEL, FALLBACK_MODEL]
    last_error = ""

    for model in models:
        try:
            # ✅ NOVO SYSTEM PROMPT - FORÇANDO ANÁLISE BASEADA EM EVIDÊNCIAS
            system_instruction = """Você é o 'GENEFIC ATS Analyzer', um especialista sênior em Engenharia de Software e Recrutamento Técnico.

**SUA MISSÃO CRÍTICA:**
Analisar repositórios GitHub e gerar relatórios **BASEADOS EM EVIDÊNCIAS CONCRETAS** encontradas no código, dependências e estrutura do projeto.

**REGRAS OBRIGATÓRIAS:**
1. **CITE EVIDÊNCIAS**: Toda afirmação deve referenciar dados reais do repositório.
   ❌ ERRADO: "O projeto demonstra boas práticas"
   ✅ CORRETO: "O projeto demonstra boas práticas evidenciadas pela presença de pasta /tests com 15 arquivos de teste e CI/CD configurado em .github/workflows"

2. **TECH SCORE JUSTIFICADO**: O score deve ser calculado com base em:
   - Complexidade das tecnologias (package.json, requirements.txt)
   - Presença de testes (pastas tests/, __tests__, spec/)
   - CI/CD configurado (.github/workflows, .gitlab-ci.yml)
   - Documentação (README completo, docs/, comentários inline)
   - Arquitetura (src/, estrutura modular, Docker)
   
3. **PROIBIDO RESPOSTAS GENÉRICAS**: 
   ❌ "bem estruturado", "código limpo", "boas práticas"
   ✅ "estrutura modular com separação src/components, src/services, src/utils"

4. **IDIOMA**: Português do Brasil

5. **FORMATO**: JSON válido com estrutura:
```json
{
  "tech_score": 0-100,
  "improvements": ["Melhoria específica 1", "Melhoria específica 2", ...],
  "ats_summary": "Narrativa profissional em 3-4 frases",
  "key_achievements": ["Conquista técnica 1 com evidência", ...],
  "technologies": ["Tech1", "Tech2", ...]
}
```

**EXEMPLOS DE ANÁLISE CORRETA:**

EXEMPLO 1 - Projeto JavaScript:
```json
{
  "tech_score": 85,
  "improvements": [
    "Adicionar testes automatizados - atualmente não há pasta /tests ou arquivos .spec.js",
    "Implementar CI/CD - não há .github/workflows para automação de deploy",
    "Dockerizar aplicação - adicionar Dockerfile para portabilidade"
  ],
  "ats_summary": "Desenvolvedor full-stack com domínio de React 18 e TypeScript evidenciado pelo package.json, implementando arquitetura modular com separação clara entre componentes (src/components), serviços API (src/services) e utilitários (src/utils). Demonstra proficiência em state management com Redux Toolkit e integração de APIs REST.",
  "key_achievements": [
    "Implementação de autenticação JWT com refresh tokens evidenciada em src/auth/",
    "Integração com 3 APIs externas (GitHub, Stripe, SendGrid) documentadas no README",
    "Arquitetura escalável com lazy loading de componentes (React.lazy em src/App.tsx)"
  ],
  "technologies": ["React 18", "TypeScript", "Redux Toolkit", "Vite", "TailwindCSS"]
}
```

EXEMPLO 2 - Projeto Python:
```json
{
  "tech_score": 72,
  "improvements": [
    "Aumentar cobertura de testes - apenas 2 arquivos em /tests para 15 módulos em /src",
    "Adicionar type hints em todas as funções para melhor manutenibilidade",
    "Documentar endpoints da API - README não contém exemplos de uso"
  ],
  "ats_summary": "Engenheiro de dados especializado em pipelines ETL com FastAPI e PostgreSQL, evidenciado pelo requirements.txt (fastapi, sqlalchemy, psycopg2). Implementa processamento assíncrono com Celery para tarefas background e demonstra conhecimento em otimização de queries SQL (migrations em /alembic).",
  "key_achievements": [
    "Pipeline ETL processando 100k+ registros/dia evidenciado por logs em /docs/performance.md",
    "API RESTful com 12 endpoints documentados em OpenAPI (src/api/openapi.yml)",
    "Deploy automatizado com Docker Compose (3 serviços: API, PostgreSQL, Redis)"
  ],
  "technologies": ["Python 3.11", "FastAPI", "PostgreSQL", "SQLAlchemy", "Docker", "Celery", "Redis"]
}
```

**AGORA ANALISE O REPOSITÓRIO ABAIXO:**
"""

            messages = [
                {'role': 'system', 'content': system_instruction},
                {'role': 'user', 'content': f"{prompt}"}
            ]

            logger.info(f"🤖 Tentando análise com modelo: {model}")
            response = ollama_client.chat(model=model, messages=messages, stream=False)
            
            content = response['message']['content']
            
            # ✅ VALIDAÇÃO DE QUALIDADE DA RESPOSTA
            if not validate_ai_response_quality(content):
                logger.warning(f"⚠️ Resposta do modelo {model} não passou na validação de qualidade. Tentando fallback...")
                continue
            
            logger.info(f"✅ Análise bem-sucedida com modelo {model}")
            return content
            
        except Exception as e:
            last_error = str(e)
            logger.warning(f"⚠️ Falha no modelo {model}: {last_error}. Tentando fallback...")
            continue
    
    logger.error(f"❌ Todos os modelos falharam. Último erro: {last_error}")
    raise RuntimeError(f"Falha total na IA: {last_error}")

def validate_ai_response_quality(response_text):
    """
    Valida se a resposta da IA é de alta qualidade e baseada em evidências.
    """
    try:
        # Extrair JSON da resposta
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not match:
            logger.warning("❌ Validação: Resposta não contém JSON válido")
            return False
        
        data = json.loads(match.group(0))
        
        # Validar estrutura obrigatória
        required_keys = ["tech_score", "improvements", "ats_summary", "key_achievements", "technologies"]
        for key in required_keys:
            if key not in data:
                logger.warning(f"❌ Validação: Chave obrigatória '{key}' ausente")
                return False
        
        # Validar que não são listas vazias
        for key in ["improvements", "key_achievements", "technologies"]:
            if not isinstance(data[key], list) or len(data[key]) == 0:
                logger.warning(f"❌ Validação: '{key}' está vazio ou não é uma lista")
                return False
        
        # ✅ VALIDAÇÃO DE QUALIDADE - Detectar respostas genéricas
        generic_terms = [
            "bem estruturado",
            "código limpo",
            "boas práticas",
            "qualidade do código",
            "bem documentado",
            "fácil de manter"
        ]
        
        full_text = json.dumps(data, ensure_ascii=False).lower()
        
        for term in generic_terms:
            if term in full_text:
                logger.warning(f"⚠️ Validação: Termo genérico detectado: '{term}'")
                # Não vamos rejeitar automaticamente, mas alertar
        
        # Validar que key_achievements e improvements têm tamanho mínimo
        for achievement in data["key_achievements"]:
            if len(achievement) < 30:  # Menos de 30 caracteres é muito curto
                logger.warning(f"⚠️ Validação: Conquista muito curta: '{achievement}'")
                return False
        
        for improvement in data["improvements"]:
            if len(improvement) < 20:
                logger.warning(f"⚠️ Validação: Melhoria muito curta: '{improvement}'")
                return False
        
        # Validar que ats_summary tem tamanho razoável
        if len(data["ats_summary"]) < 100:
            logger.warning("❌ Validação: ats_summary muito curto (< 100 chars)")
            return False
        
        # Validar que tech_score está no range correto
        if not (0 <= data["tech_score"] <= 100):
            logger.warning(f"❌ Validação: tech_score fora do range: {data['tech_score']}")
            return False
        
        logger.info("✅ Resposta passou em todas as validações de qualidade")
        return True
        
    except json.JSONDecodeError as e:
        logger.warning(f"❌ Validação: JSON inválido - {str(e)}")
        return False
    except Exception as e:
        logger.warning(f"❌ Validação: Erro inesperado - {str(e)}")
        return False

def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    if event.get("httpMethod") == "GET":
        params = event.get("queryStringParameters") or {}
        task_id = params.get("task_id")
        if not task_id: 
            return {"statusCode": 400, "headers": CORS_HEADERS, "body": json.dumps({"error": "task_id ausente"})}
        
        table = dynamodb.Table(TABLE_NAME)
        item = table.get_item(Key={"user_id": "anonymous", "timestamp": int(task_id)}).get("Item")
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps(item, cls=DecimalEncoder)}

    # Worker assíncrono
    if event.get("source") == "worker":
        task_id, repo_url = event["task_id"], event["repo_url"]
        try:
            logger.info(f"🚀 Iniciando análise do repositório: {repo_url}")
            
            # ✅ EXTRAIR CONTEXTO COMPLETO
            docs = fetch_docs(repo_url)
            
            # ✅ CHAMAR IA COM VALIDAÇÃO
            analysis = call_ollama_engine(f"Analise este repositório:\n\n{docs}")
            
            # ✅ PARSEAR E VALIDAR RESPOSTA
            match = re.search(r'\{.*\}', analysis, re.DOTALL)
            if not match: 
                raise ValueError("IA não retornou JSON válido")

            data = json.loads(match.group(0))
            
            # Validar estrutura mínima
            if "error" in data and len(data.keys()) <= 2:
                raise ValueError(f"IA retornou erro: {data['error']}")

            required_keys = ["tech_score", "improvements", "ats_summary", "key_achievements", "technologies"]
            for key in required_keys:
                if key not in data:
                    data[key] = [] if key in ["improvements", "key_achievements", "technologies"] else "Informação não disponível"
            
            # ✅ SALVAR RESULTADO NO DYNAMODB
            dynamodb.Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d, tech_score = :ts",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":val": "COMPLETED", 
                    ":d": data, 
                    ":ts": data.get("tech_score", 0)
                }
            )
            
            logger.info(f"✅ Análise concluída com sucesso! Tech Score: {data.get('tech_score')}")
            
        except GitHubRateLimitError as e:
            # ✅ TRATAMENTO ESPECÍFICO DE RATE LIMIT
            logger.error(f"❌ Rate Limit do GitHub: {str(e)}")
            dynamodb.Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":val": "FAILED",
                    ":d": {
                        "error": "GitHub Rate Limit atingido",
                        "message": str(e),
                        "solution": "Configure GITHUB_TOKEN no ambiente ou aguarde reset do rate limit"
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Falha no processamento: {str(e)}")
            dynamodb.Table(TABLE_NAME).update_item(
                Key={"user_id": "anonymous", "timestamp": int(task_id)},
                UpdateExpression="SET #s = :val, structured_data = :d",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":val": "FAILED",
                    ":d": {"error": str(e)}
                }
            )
        return {}

    # Requisição inicial (cria task)
    try:
        body = json.loads(event.get("body", "{}"))
        repo_url = body.get("repo_url")
        
        if not repo_url:
            return {
                "statusCode": 400, 
                "headers": CORS_HEADERS, 
                "body": json.dumps({"error": "repo_url é obrigatório"})
            }
        
        task_id = int(time.time())
        
        # Criar registro no DynamoDB
        dynamodb.Table(TABLE_NAME).put_item(
            Item={
                "user_id": "anonymous", 
                "timestamp": task_id, 
                "status": "PROCESSING", 
                "repo_url": repo_url
            }
        )
        
        # Invocar worker assíncrono
        lambda_client.invoke(
            FunctionName=context.function_name, 
            InvocationType="Event", 
            Payload=json.dumps({
                "source": "worker", 
                "task_id": task_id, 
                "repo_url": repo_url
            })
        )
        
        return {
            "statusCode": 202, 
            "headers": CORS_HEADERS, 
            "body": json.dumps({"task_id": task_id})
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar task: {str(e)}")
        return {
            "statusCode": 500, 
            "headers": CORS_HEADERS, 
            "body": json.dumps({"error": str(e)})
        }