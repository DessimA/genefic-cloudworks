resource "aws_api_gateway_rest_api" "portfolio_api" {
  name        = "${var.project_name}-${var.environment}-api"
  description = "API para a plataforma Portfolio Cloud Dev"
}

resource "aws_api_gateway_resource" "upload" {
  rest_api_id = aws_api_gateway_rest_api.portfolio_api.id
  parent_id   = aws_api_gateway_rest_api.portfolio_api.root_resource_id
  path_part   = "upload"
}

resource "aws_api_gateway_method" "upload_post" {
  rest_api_id   = aws_api_gateway_rest_api.portfolio_api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "upload_get" {
  rest_api_id   = aws_api_gateway_rest_api.portfolio_api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "GET"
  authorization = "NONE"
}

# ... (restante dos recursos)

resource "aws_api_gateway_integration" "lambda_upload_get" {
  rest_api_id = aws_api_gateway_rest_api.portfolio_api.id
  resource_id = aws_api_gateway_method.upload_get.resource_id
  http_method = aws_api_gateway_method.upload_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.upload_lambda_invoke_arn
}

# --- Configuração de CORS (OPTIONS) ---
resource "aws_api_gateway_method" "upload_options" {
  rest_api_id   = aws_api_gateway_rest_api.portfolio_api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "upload_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.portfolio_api.id
  resource_id = aws_api_gateway_resource.upload.id
  http_method = aws_api_gateway_method.upload_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "upload_options_200" {
  rest_api_id = aws_api_gateway_rest_api.portfolio_api.id
  resource_id = aws_api_gateway_resource.upload.id
  http_method = aws_api_gateway_method.upload_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "upload_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.portfolio_api.id
  resource_id = aws_api_gateway_resource.upload.id
  http_method = aws_api_gateway_method.upload_options.http_method
  status_code = aws_api_gateway_method_response.upload_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,file-name,project-id'",
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
  depends_on = [aws_api_gateway_integration.upload_options_integration]
}

# --- Gateway Responses para CORS em Erros ---
resource "aws_api_gateway_gateway_response" "cors_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.portfolio_api.id
  response_type = "DEFAULT_4XX"
  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'",
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
  }
}

resource "aws_api_gateway_gateway_response" "cors_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.portfolio_api.id
  response_type = "DEFAULT_5XX"
  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'",
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
  }
}
# --------------------------------------------

resource "aws_api_gateway_integration" "lambda_upload" {

  rest_api_id = aws_api_gateway_rest_api.portfolio_api.id
  resource_id = aws_api_gateway_method.upload_post.resource_id
  http_method = aws_api_gateway_method.upload_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.upload_lambda_invoke_arn
}

resource "aws_api_gateway_deployment" "portfolio_deploy" {
  depends_on = [
    aws_api_gateway_integration.lambda_upload,
    aws_api_gateway_integration.lambda_upload_get,
    aws_api_gateway_integration.upload_options_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.portfolio_api.id
}

resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.portfolio_deploy.id
  rest_api_id   = aws_api_gateway_rest_api.portfolio_api.id
  stage_name    = var.environment
}

output "api_url" {
  value = "${aws_api_gateway_stage.dev.invoke_url}/upload"
}

output "api_id" {
  value = aws_api_gateway_rest_api.portfolio_api.id
}
