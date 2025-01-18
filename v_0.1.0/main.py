import secrets
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
# pip install pyjwt

from fastapi.templating import Jinja2Templates # 
import jwt

# SECRET_KEYを同期的に生成
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"

# アプリケーション初期化
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# トークン生成リクエストのスキーマ
class TokenRequest(BaseModel):
    username: str
    

# トークン生成ロジックを共通関数にまとめる
def create_token(username: str):
    expiration = datetime.now(tz=timezone.utc) + timedelta(seconds=15)
    payload = {
        "sub": username,
        "exp": expiration,
        "iat": datetime.now(tz=timezone.utc),
        "nbf": datetime.now(tz=timezone.utc),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# POSTメソッドでトークンを生成
@app.post("/generate-token")
def generate_token(request: TokenRequest):
    try:
        token = create_token(request.username)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {e}")

# (ブラウザ用に)GETメソッドでもトークンを生成
# https://127.0.0.1:8000/generate-token?username=testuser
@app.get("/generate-token")
def generate_token_get(username: str):
    try:
        token = create_token(username)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {e}")

# トークン検証リクエストのスキーマ
class TokenVerificationRequest(BaseModel):
    token: str

# curl -X GET "http://127.0.0.1:8000/generate-token?username=testuser"

# curl -X POST "http://127.0.0.1:8000/verify-token" -H "Content-Type: application/json" -d "{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcwMDAwMDAwMCwiaWF0IjoxNzAwMDAwMDAwLCJuYmYiOjE3MDAwMDAwMDB9.abc123\"}"

# トークン検証エンドポイント
@app.post("/verify-token")
def verify_token(request: TokenVerificationRequest):
    try:
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        print("payload" + payload.json())
        return {"payload": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
