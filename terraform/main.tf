provider "aws" {
  region = var.region

  # Configurações para LocalStack
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

    endpoints {

      apigateway     = "http://localstack:4566"

      cloudfront     = "http://localstack:4566"

      dynamodb       = "http://localstack:4566"

      iam            = "http://localstack:4566"

      lambda         = "http://localstack:4566"

      s3             = "http://localstack:4566"

      sts            = "http://localstack:4566"

    }

  }

  

module "s3" {
  source      = "./modules/s3"
  bucket_name = "${var.project_name}-${var.environment}-portfolio-uploads"
}

module "dynamodb" {
  source       = "./modules/dynamodb"
  table_name   = "${var.project_name}-${var.environment}-metadata"
  project_name = var.project_name
  environment  = var.environment
}

module "iam" {
  source             = "./modules/iam"
  s3_bucket_arn      = module.s3.bucket_arn
  dynamodb_table_arn = module.dynamodb.table_arn
}

module "cloudfront" {
  count                       = var.enable_cloudfront ? 1 : 0
  source                      = "./modules/cloudfront"
  s3_bucket_website_endpoint = module.s3.website_endpoint
}

module "lambda" {
  source              = "./modules/lambda"
  project_name        = var.project_name
  environment         = var.environment
  lambda_role_arn     = module.iam.upload_role_arn
  s3_bucket_name      = module.s3.bucket_name
  dynamodb_table_name = module.dynamodb.table_name
  ai_provider         = var.ai_provider
  gemini_api_key      = var.gemini_api_key
  deepseek_api_key    = var.deepseek_api_key
}

module "api_gateway" {
  source                   = "./modules/api_gateway"
  project_name             = var.project_name
  environment              = var.environment
  upload_lambda_invoke_arn = module.lambda.upload_lambda_invoke_arn
}

variable "region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "portfolio-cloud-dev"
}

variable "environment" {
  default = "dev"
}

variable "enable_cloudfront" {
  description = "Habilitar CloudFront (desativar para LocalStack Community)"
  type        = bool
  default     = true
}

variable "ai_provider" {
  description = "Provedor de IA (aws ou gemini)"
  type        = string
  default     = "gemini"
}

variable "gemini_api_key" {
  description = "API Key do Gemini"
  type        = string
  default     = ""
}

variable "deepseek_api_key" {
  description = "API Key do DeepSeek"
  type        = string
  default     = ""
}

output "s3_bucket_name" {
  value = module.s3.bucket_name
}

output "cloudfront_domain" {
  value = var.enable_cloudfront ? module.cloudfront[0].cloudfront_domain_name : "disabled-local"
}

output "dynamodb_table_name" {
  value = module.dynamodb.table_name
}

output "upload_role_arn" {
  value = module.iam.upload_role_arn
}

output "metadata_role_arn" {

  value = module.iam.metadata_role_arn

}



output "upload_lambda_name" {



  value = module.lambda.upload_lambda_name



}







output "api_endpoint" {
  value = module.api_gateway.api_url
}

output "api_id" {
  value = module.api_gateway.api_id
}




