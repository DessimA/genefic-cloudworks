import json
import os
import sys
import pytest
import boto3
from unittest.mock import patch, MagicMock
from moto import mock_dynamodb

# Add project root to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Set environment variables BEFORE importing handler
os.environ["GROQ_API_KEY"] = "mock-key"
os.environ["PRIMARY_MODEL"] = "llama-3.3-70b-versatile"
os.environ["FALLBACK_MODEL"] = "llama-3.1-8b-instant"
os.environ["DYNAMODB_TABLE"] = "test-metadata-table"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"

from backend.lambdas.analyse.handler import handler

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"

@mock_dynamodb
def test_upload_handler_success(aws_credentials):
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1", endpoint_url="http://localhost:4566")
    table = dynamodb.create_table(
        TableName="test-metadata-table",
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "N"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    # Mock Groq Response
    mock_groq_content = json.dumps({
        "tech_score": 95,
        "improvements": ["Add tests"],
        "ats_summary": "Great project...",
        "key_achievements": ["Built a rocket"],
        "technologies": ["Python"]
    })
    
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices[0].message.content = mock_groq_content

    # Mock fetch_docs to avoid GitHub calls
    with patch("backend.lambdas.analyse.handler.fetch_docs") as mock_fetch_docs, \
         patch("backend.lambdas.analyse.handler.groq_client.chat.completions.create") as mock_groq_create, \
         patch("backend.lambdas.analyse.handler.lambda_client.invoke") as mock_lambda_invoke:
        
        mock_fetch_docs.return_value = "Mocked Repository Content"
        mock_groq_create.return_value = mock_chat_completion

        # 1. Test Initial Request (creates task)
        event_init = {
            "body": json.dumps({"repo_url": "https://github.com/DessimA/quizlab"}),
            "httpMethod": "POST",
        }
        # Mock Context
        mock_context = MagicMock()
        mock_context.function_name = "test-func"
        
        response_init = handler(event_init, mock_context)
        assert response_init["statusCode"] == 202
        task_id = json.loads(response_init["body"])["task_id"]

        # 2. Test Worker Execution (processes task)
        event_worker = {
            "source": "worker",
            "task_id": task_id,
            "repo_url": "https://github.com/DessimA/quizlab"
        }
        handler(event_worker, None)

        # Verify DynamoDB update
        items = table.scan()["Items"]
        assert len(items) == 1
        assert items[0]["status"] == "COMPLETED"
        assert items[0]["tech_score"] == 95
        assert items[0]["repo_url"] == "https://github.com/DessimA/quizlab"

@mock_dynamodb
def test_upload_handler_missing_url(aws_credentials):
    event = {
        "body": json.dumps({}),
        "httpMethod": "POST",
    }
    response = handler(event, MagicMock())
    assert response["statusCode"] == 400
    assert "error" in json.loads(response["body"])

@mock_dynamodb
def test_upload_handler_groq_failure(aws_credentials):
     # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1", endpoint_url="http://localhost:4566")
    table = dynamodb.create_table(
        TableName="test-metadata-table",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}, {"AttributeName": "timestamp", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}, {"AttributeName": "timestamp", "AttributeType": "N"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    with patch("backend.lambdas.analyse.handler.fetch_docs") as mock_fetch_docs, \
         patch("backend.lambdas.analyse.handler.groq_client.chat.completions.create") as mock_groq_create:
        
        mock_fetch_docs.return_value = "Mocked Content"
        mock_groq_create.side_effect = Exception("Groq Down")

        # Create initial task first
        table.put_item(Item={
            "user_id": "anonymous",
            "timestamp": 123456,
            "status": "PROCESSING",
            "repo_url": "https://github.com/DessimA/quizlab"
        })

        event_worker = {
            "source": "worker",
            "task_id": 123456,
            "repo_url": "https://github.com/DessimA/quizlab"
        }

        handler(event_worker, None)
        
        # Verify failure status
        item = table.get_item(Key={"user_id": "anonymous", "timestamp": 123456})["Item"]
        assert item["status"] == "FAILED"
        assert "Groq Down" in str(item["structured_data"]["error"])