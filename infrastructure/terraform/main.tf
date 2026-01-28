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

module "lambda" {
  source              = "./modules/lambda"
  project_name        = var.project_name
  environment         = var.environment
  lambda_role_arn     = module.iam.upload_role_arn
  s3_bucket_name      = module.s3.bucket_name
  dynamodb_table_name = module.dynamodb.table_name
  ollama_endpoint     = var.ollama_endpoint
  primary_model       = var.primary_model
  fallback_model      = var.fallback_model
  ollama_api_key      = var.ollama_api_key
  github_token        = var.github_token
}

module "api_gateway" {
  source                   = "./modules/api_gateway"
  project_name             = var.project_name
  environment              = var.environment
  upload_lambda_invoke_arn = module.lambda.upload_lambda_invoke_arn
}