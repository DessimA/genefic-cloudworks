# Lambda Execution Role - Upload
resource "aws_iam_role" "upload_lambda_role" {
  name = "upload_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "upload_s3_policy" {
  name        = "upload_s3_policy"
  description = "Permissions for upload lambda to write to S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:PutObject", "s3:PutObjectAcl"]
        Effect   = "Allow"
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "upload_s3_attach" {
  role       = aws_iam_role.upload_lambda_role.name
  policy_arn = aws_iam_policy.upload_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "upload_db_attach" {
  role       = aws_iam_role.upload_lambda_role.name
  policy_arn = aws_iam_policy.metadata_dynamodb_policy.arn
}

# Lambda Execution Role - Metadata
resource "aws_iam_role" "metadata_lambda_role" {
  name = "metadata_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "metadata_dynamodb_policy" {
  name        = "metadata_dynamodb_policy"
  description = "Permissions for metadata lambda to access DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Effect   = "Allow"
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "metadata_db_attach" {
  role       = aws_iam_role.metadata_lambda_role.name
  policy_arn = aws_iam_policy.metadata_dynamodb_policy.arn
}

# Common CloudWatch Logs policy
resource "aws_iam_policy" "lambda_logging_policy" {
  name        = "lambda_logging_policy"
  description = "IAM policy for logging from a lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "upload_logging_attach" {
  role       = aws_iam_role.upload_lambda_role.name
  policy_arn = aws_iam_policy.lambda_logging_policy.arn
}

resource "aws_iam_role_policy_attachment" "metadata_logging_attach" {
  role       = aws_iam_role.metadata_lambda_role.name
  policy_arn = aws_iam_policy.lambda_logging_policy.arn
}

output "upload_role_arn" {
  value = aws_iam_role.upload_lambda_role.arn
}

output "metadata_role_arn" {
  value = aws_iam_role.metadata_lambda_role.arn
}