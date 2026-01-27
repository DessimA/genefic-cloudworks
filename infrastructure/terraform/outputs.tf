output "s3_bucket_name" {
  value = module.s3.bucket_name
}

output "dynamodb_table_name" {
  value = module.dynamodb.table_name
}

output "upload_role_arn" {
  value = module.iam.upload_role_arn
}

output "api_endpoint" {
  value = module.api_gateway.api_url
}

output "api_id" {
  value = module.api_gateway.api_id
}
