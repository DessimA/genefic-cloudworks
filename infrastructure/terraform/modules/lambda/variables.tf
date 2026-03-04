variable "project_name" {}
variable "environment" {}
variable "lambda_role_arn" {}
variable "s3_bucket_name" {}
variable "dynamodb_table_name" {}

variable "primary_model" {
  description = "Modelo principal"
  type        = string
}

variable "fallback_model" {
  description = "Modelo de fallback"
  type        = string
}

variable "groq_api_key" {
  description = "Chave de API do Groq"
  type        = string
  sensitive   = true
}

variable "github_token" {
  description = "GitHub Token"
  type        = string
  default     = ""
}
