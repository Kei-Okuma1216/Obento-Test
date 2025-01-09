import jwt
from datetime import date,datetime, timedelta, timezone

def function1():
    """二つの数値を足し合わせる関数"""
    return "これは function1 です。"


import os
SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")
#SECRET_KEY = "your-secret-key"

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


