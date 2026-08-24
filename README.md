# genefic-cloudworks

Plataforma de engenharia de carreira AI-Native com arquitetura 100% serverless event-driven na AWS. O backend utiliza AWS Lambda em Python com Groq Cloud (Llama 3) para analise de repositorios GitHub, extraindo DNA tecnico e gerando scores. Infraestrutura gerenciada via Terraform modular, com DynamoDB para persistencia, API Gateway e frontend SPA no S3.

**Stack:** Python, AWS Lambda, Terraform, DynamoDB, Groq, S3