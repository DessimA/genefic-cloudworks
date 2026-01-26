variable "project_name" {}
variable "environment" {}
variable "lambda_role_arn" {}
variable "s3_bucket_name" {}
variable "dynamodb_table_name" {}
variable "ai_provider" { default = "gemini" }
variable "gemini_api_key" { default = "" }
variable "deepseek_api_key" { default = "" }
