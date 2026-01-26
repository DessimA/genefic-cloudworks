# Sprint 1 Architecture: Infrastructure Configuration

## Overview
Focus on setting up the core storage and distribution infrastructure using Terraform.

## Components
- **IAM Roles**: Least-privilege roles for Lambda functions and S3 bucket access.
- **S3 Bucket**: Configured for static website hosting with public read access.
- **CloudFront**: Distribution to serve S3 content globally with HTTPS.

## Security
- No public access to S3 directly (Origin Access Identity/Control).
- HTTPS enforced by CloudFront.
- IAM policies strictly limited to required actions.
