variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for uploads"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for metadata"
  type        = string
}
