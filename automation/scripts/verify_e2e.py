import requests
import json
import os
import sys
import boto3
import time

# Configuration
LOCALSTACK_HOST = os.environ.get("LOCALSTACK_HOST", "localstack")
LOCALSTACK_ENDPOINT = f"http://{LOCALSTACK_HOST}:4566"
TARGET_REPO = "https://github.com/DessimA/quizlab"
EXPECTED_REPO_NAME = "quizlab"

def get_api_endpoint():
    """Retrieves the API Gateway endpoint from LocalStack."""
    client = boto3.client("apigateway", endpoint_url=LOCALSTACK_ENDPOINT, region_name="us-east-1",
                          aws_access_key_id="test", aws_secret_access_key="test")
    
    apis = client.get_rest_apis()
    if not apis['items']:
        raise Exception("No APIs found in LocalStack.")
    
    api_id = apis['items'][0]['id']
    # Construct the local URL format for LocalStack
    # http://localhost:4566/restapis/{api_id}/{stage_name}/_user_request_/{resource_path}
    return f"{LOCALSTACK_ENDPOINT}/restapis/{api_id}/dev/_user_request_/upload"

def run_e2e_test():
    print(f"--- 🚀 Starting E2E Verification for {TARGET_REPO} ---")
    
    try:
        # 1. Discover API Endpoint
        print("--- 🔍 Discovering API Endpoint... ---")
        url = get_api_endpoint()
        print(f"Target URL: {url}")
        
        # 2. Send Request
        print(f"--- 📡 Sending Request (Timeout: 120s for AI processing)... ---")
        payload = {"repo_url": TARGET_REPO}
        headers = {"Content-Type": "application/json"}
        
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        duration = time.time() - start_time
        
        print(f"--- ⏱️ Response received in {duration:.2f}s ---")
        
        # 3. Validate Response Code
        if response.status_code != 200:
            print(f"❌ FAILED: Status Code {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
            
        # 4. Validate Response Body
        data = response.json()
        print(f"--- 📦 Response Data: ---")
        print(json.dumps(data, indent=2))
        
        if data.get("repo_name") != EXPECTED_REPO_NAME:
            print(f"❌ FAILED: Expected repo_name '{EXPECTED_REPO_NAME}', got '{data.get('repo_name')}'")
            sys.exit(1)
            
        if "analysis" not in data or not data["analysis"]:
             print(f"❌ FAILED: 'analysis' field is missing or empty.")
             sys.exit(1)

        # Check if it was a fallback error message
        if "Falha técnica" in data["analysis"] or "Erro" in data["analysis"]:
             print(f"⚠️ WARNING: The request succeeded but returned an error message from the AI/Logic layer.")
             # We might want to fail here depending on strictness. 
             # For "chance real de funcionar", this is a fail.
             print("❌ FAILED: AI generation failed (see analysis output).")
             sys.exit(1)
             
        print("\n✅ SUCCESS: E2E Test Passed! System is fully operational.")
        
    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure boto3 can connect to LocalStack
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    run_e2e_test()
