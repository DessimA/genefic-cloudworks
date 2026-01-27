# GENEFIC Cloudworks - ATS Optimizer 🚀

Plataforma Serverless de análise inteligente de repositórios GitHub. Transformamos código e documentação técnica em narrativas de alto impacto para currículos e portfólios profissionais, otimizando a visibilidade em sistemas de triagem (ATS).

## 🌟 Estado Atual (MVP Consolidado)

A aplicação foi totalmente reorganizada para uma arquitetura escalável e resiliente, utilizando o estado da arte em simulação Cloud e Inteligência Artificial.

### Funcionalidades Principais:
- **Análise Assíncrona:** Workflow desacoplado (API Gateway -> Lambda Trigger -> Lambda Worker).
- **IA com Fallback:** Motor de IA robusto com tentativa primária em `gpt-oss:120b-cloud` e fallback automático para `deepseek-v3.1:671b-cloud`.
- **Feedback Visual Dinâmico:** Dashboard moderno com gauge de Tech Score e notificações em tempo real (Toast).
- **Processamento de Metadados:** Extração profunda de READMEs e metadados via GitHub API.

## 🛠️ Stack Tecnológica
- **Backend:** Python 3.11 (AWS Lambda)
- **Infraestrutura como Código:** Terraform (Provider AWS ~> 6.0)
- **Simulação Cloud:** LocalStack (S3, DynamoDB, API Gateway, IAM)
- **Inteligência Artificial:** Ollama (Host-native) com suporte a modelos Cloud.
- **Frontend:** Vanilla JavaScript ES6+, CSS Moderno (Glassmorphism).

## 🏗️ Estrutura do Projeto
```text
genefic-cloudworks/
├── automation/
│   ├── scripts/          # Deploy, Destroy, Lint e Testes
│   └── docker/           # Configurações de containers auxiliares
├── backend/
│   ├── lambdas/          # Funções (Auth, Analyse, Import, Generate, Deploy)
│   ├── shared/           # Adapters de IA e utilitários comuns
│   └── tests/            # Testes Unitários e Integração
├── frontend/
│   ├── public/           # Dashboard, Assets, CSS e JS
│   └── templates/        # Templates HTML para portfólios gerados
├── infrastructure/
│   ├── terraform/        # Módulos e configurações de infraestrutura
│   └── local/            # Docker Compose para ambiente de desenvolvimento
└── organize_structure.ps1 # Script de consolidação da arquitetura
```

## 📦 Como Executar (Ambiente Local)

### Pré-requisitos
- **Docker & Docker Compose** instalados.
- **Ollama** rodando nativamente no Host (Windows).
- Modelos baixados: `ollama pull llama3.2` (ou os modelos cloud configurados).

### Passo a Passo
1.  **Organize a estrutura:**
    ```powershell
    ./organize_structure.ps1
    ```
2.  **Configure o ambiente:**
    Copie o `.env.example` para `.env` e preencha sua `OLLAMA_API_KEY`.
3.  **Deploy Automático:**
    ```bash
    ./automation/scripts/deploy-local.sh
    ```
4.  **Acesse o Dashboard:**
    URL fornecida ao final do log de deploy (ex: `http://genefic-cloudworks-local-portfolio-uploads.s3-website.localhost.localstack.cloud:4566`).

## 🚀 Pontos de Melhoria Futura
- [ ] **GitHub OAuth 2.0:** Implementação do fluxo de login real via Lambda `auth`.
- [ ] **Exportação de PDF:** Gerar versão para download do resumo ATS.
- [ ] **Integração Amazon Bedrock:** Adapter para Claude 3 Haiku em produção.
- [ ] **Notificações Push:** WebSocket para atualização de status da análise sem polling.

## 📄 Licença
Projeto desenvolvido para fins educacionais e demonstração técnica de arquitetura Cloud Serverless e IA.
