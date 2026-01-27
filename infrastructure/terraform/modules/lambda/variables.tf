variable "project_name" {}
variable "environment" {}
variable "lambda_role_arn" {}
variable "s3_bucket_name" {}
variable "dynamodb_table_name" {}
variable "ollama_endpoint" { default = "http://host.docker.internal:11434" }
variable "ollama_model" { default = "gpt-oss:120b-cloud" }
variable "ollama_api_key" {}