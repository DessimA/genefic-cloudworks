variable "project_name" {}
variable "environment" {}
variable "lambda_role_arn" {}
variable "s3_bucket_name" {}
variable "dynamodb_table_name" {}

variable "ollama_endpoint" {
  description = "Endpoint do Ollama"
  type        = string
}

variable "primary_model" {
  description = "Modelo principal"
  type        = string
}

variable "fallback_model" {
  description = "Modelo de fallback"
  type        = string
}

variable "ollama_api_key" {
  description = "Chave de API do Ollama"
  type        = string
  default     = ""
}

variable "github_token" {
  description = "GitHub Token"
  type        = string
  default     = ""
}
