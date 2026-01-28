import requests
import time
import json
import statistics
import os

def get_api_id():
    """Tenta obter o ID da API do ambiente ou dinamicamente do LocalStack"""
    env_id = os.environ.get("API_ID")
    if env_id: return env_id
    
    try:
        # Dentro da rede docker o host é genefic-localstack
        resp = requests.get("http://genefic-localstack:4566/_aws/execute-api/")
        data = resp.json()
        # Pega a primeira API encontrada
        return data["apis"][0]["id"]
    except Exception:
        # Fallback se não conseguir listar
        return "ngq6hgcuqf"

# Configurações do Teste
API_ID = get_api_id()
API_URL = f"http://genefic-localstack:4566/_aws/execute-api/{API_ID}/local/upload"
REPOS = [
    "https://github.com/DessimA/quizlab",
    "https://github.com/DessimA/NASA_Galery",
    "https://github.com/DessimA/literalura"
]
ATTEMPTS_PER_REPO = 3

def run_analysis(repo_url):
    print(f"🚀 Analisando: {repo_url}")
    try:
        resp = requests.post(API_URL, json={"repo_url": repo_url})
        if resp.status_code != 202:
            print(f"❌ Erro POST: {resp.status_code}")
            return None
        
        task_id = resp.json()["task_id"]
        
        # Polling
        max_retries = 30
        for _ in range(max_retries):
            time.sleep(5)
            status_resp = requests.get(f"{API_URL}?task_id={task_id}")
            result = status_resp.json()
            
            if result.get("status") == "COMPLETED":
                score = result.get("tech_score", 0)
                print(f"✅ Score: {score}")
                return score
            elif result.get("status") == "FAILED":
                print(f"❌ Falha: {result.get('structured_data', {}).get('error')}")
                return 0
        return 0
            
    except Exception as e:
        print(f"💥 Erro: {e}")
        return None

def main():
    print(f"📍 Usando API URL: {API_URL}")
    report = {}
    
    for repo in REPOS:
        scores = []
        print(f"\n--- 📋 Testando: {repo} ---")
        for i in range(ATTEMPTS_PER_REPO):
            print(f"Tentativa {i+1}/{ATTEMPTS_PER_REPO}")
            score = run_analysis(repo)
            if score is not None: scores.append(score)
        
        if scores:
            report[repo] = {
                "scores": scores,
                "avg": statistics.mean(scores),
                "stdev": statistics.stdev(scores) if len(scores) > 1 else 0
            }

    print("\n" + "="*50)
    print("📊 RELATÓRIO DE CONSISTÊNCIA FINAL")
    print("="*50)
    for repo, data in report.items():
        print(f"\nRepo: {repo}")
        print(f"Scores: {data['scores']} | Média: {data['avg']:.2f} | Desvio: {data['stdev']:.2f}")
        if data['stdev'] > 15:
            print("⚠️ ALTA VARIÂNCIA!")
        else:
            print("✅ CONSISTÊNCIA OK.")
    print("="*50)

if __name__ == "__main__":
    main()