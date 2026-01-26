import boto3
import os

def check_infra():
    endpoint = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")
    print(f"Checking infrastructure at {endpoint}...")
    
    s3 = boto3.client("s3", endpoint_url=endpoint, region_name="us-east-1")
    ddb = boto3.client("dynamodb", endpoint_url=endpoint, region_name="us-east-1")
    
    try:
        buckets = s3.list_buckets()["Buckets"]
        print(f"S3 Buckets: {[b['Name'] for b in buckets]}")
        
        tables = ddb.list_tables()["TableNames"]
        print(f"DynamoDB Tables: {tables}")
        
        print("Infrastructure check complete!")
    except Exception as e:
        print(f"Error checking infrastructure: {e}")

if __name__ == "__main__":
    check_infra()
