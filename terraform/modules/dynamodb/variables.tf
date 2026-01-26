variable "table_name" {
  description = "The name of the DynamoDB table"
  type        = string
}

variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "The environment (e.g., dev, prod)"
  type        = string
}
