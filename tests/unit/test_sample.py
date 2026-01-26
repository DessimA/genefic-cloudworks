import boto3
import pytest
from moto import mock_s3

@mock_s3
def test_s3_bucket_creation():
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket_name = "test-bucket"
    s3.create_bucket(Bucket=bucket_name)
    
    response = s3.list_buckets()
    buckets = [bucket["Name"] for bucket in response["Buckets"]]
    assert bucket_name in buckets
