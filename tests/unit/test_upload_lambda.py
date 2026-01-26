import json
import base64
import pytest
import boto3
from moto import mock_s3, mock_dynamodb
from src.lambda.upload.handler import handler

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    import os
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["BUCKET_NAME"] = "test-bucket"
    os.environ["DYNAMODB_TABLE"] = "test-table"

@mock_s3
@mock_dynamodb
def test_upload_handler_success(aws_credentials):
    # Setup mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-bucket")

    # Setup mock DynamoDB
    db = boto3.resource("dynamodb", region_name="us-east-1")
    db.create_table(
        TableName="test-table",
        KeySchema=[
            {"AttributeName": "project_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "project_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "N"}
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1}
    )

    # Mock event
    file_content = b"hello world"
    encoded_content = base64.b64encode(file_content).decode("utf-8")
    event = {
        "body": encoded_content,
        "isBase64Encoded": True,
        "headers": {
            "file-name": "test.txt",
            "Content-Type": "text/plain",
            "project-id": "proj-123"
        }
    }

    # Call handler
    response = handler(event, None)

    # Verify response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Upload e registro concluídos"

    # Verify S3 content
    obj = s3.get_object(Bucket="test-bucket", Key="uploads/proj-123/test.txt")
    assert obj["Body"].read() == file_content

    # Verify DynamoDB metadata
    table = db.Table("test-table")
    items = table.scan()["Items"]
    assert len(items) == 1
    assert items[0]["project_id"] == "proj-123"
    assert items[0]["filename"] == "test.txt"
    assert items[0]["status"] == "UPLOADED"
