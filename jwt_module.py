import os
import jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def function1():
    """二つの数値を足し合わせる関数"""
    return "これは function1 です。"


SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")
#SECRET_KEY = "your-secret-key"

# 秘密鍵my-local.keyをファイルから読み込む関数:
def load_private_key(key_file: str): 
    with open(key_file, "rb") as key_file:
        private_key = load_pem_private_key(key_file.read(), password=None) 
        return private_key 

private_key = load_private_key("./my-local.key")

# 備考：crtファイルはuvicorn起動だけで使っているため。
#certificate = load_certificate("./my-local.crt")

# JWTの生成関数
def create_jwt(username: str, password: str, date: datetime):
    payload = {
        "username": username,
        "password": password,
        "date": str(date),
        "exp": datetime.now(tz=timezone.utc) + timedelta(days=1)  # 有効期限を設定
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# JWTの検証関数
def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


