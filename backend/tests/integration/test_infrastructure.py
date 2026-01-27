import boto3
import pytest
import os
import requests
import json
import time

# Use LocalStack endpoint
ENDPOINT_URL = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")
AWS_REGION = "us-east-1"

@pytest.fixture
def s3_client():
    return boto3.client("s3", endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)

@pytest.fixture
def dynamodb_client():
    return boto3.client("dynamodb", endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)

@pytest.fixture
def apigateway_client():
    return boto3.client("apigateway", endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)

def test_s3_bucket_exists(s3_client):
    # Retrieve bucket name dynamically if possible, or assume standard naming convention
    # project-env-portfolio-uploads
    bucket_name = "portfolio-cloud-dev-dev-portfolio-uploads"
    try:
        response = s3_client.head_bucket(Bucket=bucket_name)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except Exception as e:
        # If bucket listing is allowed, print available buckets for debugging
        buckets = s3_client.list_buckets()
        print(f"Available buckets: {[b['Name'] for b in buckets['Buckets']]}")
        pytest.fail(f"Bucket {bucket_name} not found: {e}")

def test_dynamodb_table_exists(dynamodb_client):
    table_name = "portfolio-cloud-dev-dev-metadata"
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        assert response["Table"]["TableStatus"] == "ACTIVE"
    except Exception as e:
        tables = dynamodb_client.list_tables()
        print(f"Available tables: {tables['TableNames']}")
        pytest.fail(f"Table {table_name} not found: {e}")

def test_api_gateway_redeployed(apigateway_client):
    # Verify we have at least one API deployed
    apis = apigateway_client.get_rest_apis()
    assert len(apis['items']) > 0, "No API Gateway APIs found"
    
    api_id = apis['items'][0]['id']
    print(f"Found API ID: {api_id}")
    
    # Verify 'upload' resource exists
    resources = apigateway_client.get_resources(restApiId=api_id)
    upload_resource = next((r for r in resources['items'] if r.get('path') == '/upload'), None)
    assert upload_resource is not None, "/upload resource not found in API Gateway"