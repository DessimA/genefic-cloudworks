data "archive_file" "upload_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../../backend/lambdas/dist"
  output_path = "${path.module}/../../../../backend/lambdas/lambda.zip"
}

resource "aws_lambda_function" "upload_lambda" {
  filename         = data.archive_file.upload_lambda_zip.output_path
  source_code_hash = data.archive_file.upload_lambda_zip.output_base64sha256
  function_name    = "${var.project_name}-${var.environment}-upload"
  role             = var.lambda_role_arn
  handler          = "handler.handler"
  runtime          = "python3.11"
  timeout          = 300

  environment {
    variables = {
      BUCKET_NAME             = var.s3_bucket_name
      DYNAMODB_TABLE          = var.dynamodb_table_name
      OLLAMA_ENDPOINT         = var.ollama_endpoint
      OLLAMA_MODEL            = var.ollama_model
      OLLAMA_API_KEY          = var.ollama_api_key
      POWERTOOLS_SERVICE_NAME = "analyze-service"
    }
  }
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_lambda.function_name
  principal     = "apigateway.amazonaws.com"
}

output "upload_lambda_arn" {
  value = aws_lambda_function.upload_lambda.arn
}

output "upload_lambda_name" {
  value = aws_lambda_function.upload_lambda.function_name
}

output "upload_lambda_invoke_arn" {
  value = aws_lambda_function.upload_lambda.invoke_arn
}
