import json
import os
import pytest
import boto3
from unittest.mock import patch, MagicMock
from moto import mock_dynamodb

# Set environment variables BEFORE importing handler
os.environ["AI_PROVIDER"] = "ollama"
os.environ["OLLAMA_ENDPOINT"] = "http://mock-ollama:11434/v1/chat/completions"
os.environ["OLLAMA_MODEL"] = "llama3.2"
os.environ["DYNAMODB_TABLE"] = "test-metadata-table"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

from src.functions.upload.handler import handler

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
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="test-metadata-table",
        KeySchema=[
            {"AttributeName": "project_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "project_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "N"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    # Mock Ollama Response
    mock_ollama_response = {
        "choices": [
            {
                "message": {
                    "content": "Narrativa Profissional: Este projeto é um Quiz..."
                }
            }
        ]
    }

    # Patch urllib.request.urlopen to mock Ollama API call
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_ollama_response).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Mock event
        event = {
            "body": json.dumps({"repo_url": "https://github.com/DessimA/quizlab"}),
            "httpMethod": "POST",
        }

        # Call handler
        response = handler(event, None)

        # Assertions
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        
        assert "analysis" in body
        assert body["repo_name"] == "quizlab"
        assert body["tech_score"] == 100
        assert "Narrativa Profissional" in body["analysis"]

        # Verify DynamoDB persistence
        items = table.scan()["Items"]
        assert len(items) == 1
        assert items[0]["repo_name"] == "quizlab"
        assert items[0]["analysis"] == body["analysis"]

@mock_dynamodb
def test_upload_handler_missing_url(aws_credentials):
    event = {
        "body": json.dumps({}),
        "httpMethod": "POST",
    }
    response = handler(event, None)
    assert response["statusCode"] == 400
    assert "error" in json.loads(response["body"])

@mock_dynamodb
def test_upload_handler_ollama_failure(aws_credentials):
     # Setup mock DynamoDB (needed because handler initializes resource)
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="test-metadata-table",
        KeySchema=[{"AttributeName": "project_id", "KeyType": "HASH"}, {"AttributeName": "timestamp", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": "project_id", "AttributeType": "S"}, {"AttributeName": "timestamp", "AttributeType": "N"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = Exception("Ollama Down")

        event = {
            "body": json.dumps({"repo_url": "https://github.com/DessimA/quizlab"}),
            "httpMethod": "POST",
        }

        response = handler(event, None)
        
        # Handler should still return success but with error message in analysis
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "Falha técnica na análise IA" in body["analysis"]