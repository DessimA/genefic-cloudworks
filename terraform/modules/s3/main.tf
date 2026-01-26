resource "aws_s3_bucket" "portfolio_bucket" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_versioning" "portfolio_versioning" {
  bucket = aws_s3_bucket.portfolio_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "portfolio_lifecycle" {
  bucket = aws_s3_bucket.portfolio_bucket.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "portfolio_cors" {
  bucket = aws_s3_bucket.portfolio_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["*"] # In production, restrict this to your domain
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_website_configuration" "portfolio_website" {
  bucket = aws_s3_bucket.portfolio_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_public_access_block" "portfolio_access" {
  bucket = aws_s3_bucket.portfolio_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "portfolio_policy" {
  bucket = aws_s3_bucket.portfolio_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.portfolio_bucket.arn}/*"
      },
    ]
  })
  depends_on = [aws_s3_bucket_public_access_block.portfolio_access]
}

output "bucket_name" {
  value = aws_s3_bucket.portfolio_bucket.id
}

output "bucket_arn" {
  value = aws_s3_bucket.portfolio_bucket.arn
}

output "website_endpoint" {
  value = aws_s3_bucket_website_configuration.portfolio_website.website_endpoint
}
