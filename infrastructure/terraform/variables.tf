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

variable "ollama_model" {
  description = "Modelo a ser usado no Ollama"
  type        = string
  default     = "gpt-oss:120b-cloud"
}

variable "ollama_api_key" {
  description = "Chave de API do Ollama Cloud"
  type        = string
  default     = ""
}
