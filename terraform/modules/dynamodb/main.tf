resource "aws_dynamodb_table" "users" {
  name           = "${var.project_name}-${var.environment}-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "email"

  attribute {
    name = "email"
    type = "S"
  }
}

resource "aws_dynamodb_table" "portfolio_metadata" {
  name           = var.table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "timestamp"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

output "table_arn" {
  value = aws_dynamodb_table.portfolio_metadata.arn
}

output "table_name" {
  value = aws_dynamodb_table.portfolio_metadata.name
}

output "users_table_name" {
  value = aws_dynamodb_table.users.name
}
