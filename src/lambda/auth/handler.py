import json
import os
import uuid
import jwt
import bcrypt
import boto3
from datetime import datetime, timedelta
from aws_lambda_powertools import Logger

logger = Logger()
dynamodb = boto3.resource("dynamodb")
USER_TABLE = os.environ.get("USER_TABLE")
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key")

def handler(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "")
    
    try:
        body = json.loads(event.get("body", "{}"))
        
        if "/auth/register" in path and method == "POST":
            return register(body)
        elif "/auth/login" in path and method == "POST":
            return login(body)
        
        return {"statusCode": 404, "body": json.dumps({"error": "Not Found"})}
    except Exception as e:
        logger.exception("Auth error")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def register(data):
    table = dynamodb.Table(USER_TABLE)
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return {"statusCode": 400, "body": json.dumps({"error": "Email e senha obrigatórios"})}
    
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    table.put_item(Item={
        "user_id": str(uuid.uuid4()),
        "email": email,
        "password": hashed.decode('utf-8'),
        "created_at": datetime.now().isoformat()
    })
    
    return {"statusCode": 201, "body": json.dumps({"message": "Usuário criado com sucesso"})}

def login(data):
    table = dynamodb.Table(USER_TABLE)
    email = data.get("email")
    password = data.get("password")
    
    response = table.get_item(Key={"email": email})
    user = response.get("Item")
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        return {"statusCode": 401, "body": json.dumps({"error": "Credenciais inválidas"})}
    
    token = jwt.encode({
        "user_id": user["user_id"],
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }, JWT_SECRET, algorithm="HS256")
    
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Set-Cookie": f"auth_token={token}; HttpOnly; Secure; SameSite=Strict; Max-Age=604800"
        },
        "body": json.dumps({"token": token, "user": {"email": email}})
    }
