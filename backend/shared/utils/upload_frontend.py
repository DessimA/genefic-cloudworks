import boto3
import os
import sys
import mimetypes

def upload_dir(bucket_name, source_dir):
    endpoint = os.environ.get("LOCALSTACK_ENDPOINT", "http://localstack:4566")
    s3 = boto3.client("s3", endpoint_url=endpoint, region_name="us-east-1")
    
    print(f"Fazendo upload de {source_dir} para o bucket {bucket_name}...")
    
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, source_dir)
            
            # Determina o Content-Type
            content_type, _ = mimetypes.guess_type(local_path)
            if content_type is None:
                content_type = 'binary/octet-stream'
            
            s3.upload_file(
                local_path, 
                bucket_name, 
                relative_path,
                ExtraArgs={'ContentType': content_type}
            )
            print(f"  - {relative_path} ({content_type})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python upload_frontend.py <bucket_name>")
        sys.exit(1)
    
    bucket = sys.argv[1]
    frontend_path = "frontend"
    upload_dir(bucket, frontend_path)
