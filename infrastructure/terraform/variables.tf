variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project Name"
  type        = string
  default     = "genefic-cloudworks"
}

variable "environment" {
  description = "Environment (local/prod)"
  type        = string
  default     = "local"
}

variable "aws_endpoint" {
  description = "AWS Endpoint for LocalStack"
  type        = string
  default     = "http://localstack:4566"
}

variable "ollama_endpoint" {
  description = "Endpoint do Ollama"
  type        = string
  default     = "http://ollama:11434"
}

variable "primary_model" {
  description = "Modelo principal a ser usado no Ollama"
  type        = string
}

variable "fallback_model" {
  description = "Modelo de fallback a ser usado no Ollama"
  type        = string
}

variable "ollama_api_key" {
  description = "Chave de API do Ollama Cloud"
  type        = string
  default     = ""
}

variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  default     = ""
}
