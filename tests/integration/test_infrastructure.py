import boto3
import pytest
import os

# Use LocalStack endpoint if running in Docker/LocalStack env
ENDPOINT_URL = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")

@pytest.fixture
def s3_client():
    return boto3.client("s3", endpoint_url=ENDPOINT_URL, region_name="us-east-1")

@pytest.fixture
def dynamodb_client():
    return boto3.client("dynamodb", endpoint_url=ENDPOINT_URL, region_name="us-east-1")

@pytest.fixture
def iam_client():
    return boto3.client("iam", endpoint_url=ENDPOINT_URL, region_name="us-east-1")

def test_s3_bucket_exists(s3_client):
    # This assumes the bucket name from our terraform/main.tf default
    bucket_name = "portfolio-cloud-dev-dev-portfolio-uploads"
    try:
        response = s3_client.head_bucket(Bucket=bucket_name)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except Exception as e:
        pytest.fail(f"Bucket {bucket_name} does not exist or is not accessible: {e}")

def test_dynamodb_table_exists(dynamodb_client):
    table_name = "portfolio-cloud-dev-dev-metadata"
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        assert response["Table"]["TableStatus"] == "ACTIVE"
    except Exception as e:
        pytest.fail(f"Table {table_name} does not exist: {e}")

def test_iam_roles_exist(iam_client):
    roles = ["upload_lambda_role", "metadata_lambda_role"]
    for role_name in roles:
        try:
            response = iam_client.get_role(RoleName=role_name)
            assert response["Role"]["RoleName"] == role_name
        except Exception as e:
            pytest.fail(f"IAM Role {role_name} does not exist: {e}")
