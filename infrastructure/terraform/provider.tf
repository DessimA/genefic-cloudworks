terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  dynamic "endpoints" {
    for_each = var.environment == "local" ? [1] : []
    content {
      apigateway     = var.aws_endpoint
      cloudfront     = var.aws_endpoint
      dynamodb       = var.aws_endpoint
      iam            = var.aws_endpoint
      lambda         = var.aws_endpoint
      s3             = var.aws_endpoint
      sts            = var.aws_endpoint
    }
  }
}
