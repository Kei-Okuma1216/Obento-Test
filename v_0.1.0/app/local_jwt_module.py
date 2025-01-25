from functools import wraps
import logging
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from datetime import date, datetime, timedelta, timezone
import jwt
import os

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY", "3a5e8e2b7c9d5f7b6a1b2e9f8e2d6c3e4f5a6b7c8d9e0a1b2c3d4e5f6a7b8c9d")
TOKEN_EXPIRE_MINUTES = 15
TOKEN_EXPIRE_DAYS = 30

# ログ用の設定
logging.basicConfig(level=logging.INFO)

# カスタムデコレーターを定義
def log_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logging.info("- %s 前", func.__name__)
        result = await func(*args, **kwargs)
        logging.info("- %s 後", func.__name__)
        return result
    return wrapper

# 秘密鍵my-local.keyをファイルから読む
def load_private_key(key_file: str): 
    with open(key_file, "rb") as key_file:
        private_key = load_pem_private_key(key_file.read(), password=None) 
        return private_key 

private_key = load_private_key("./my-local.key")


# 秘密鍵を元に署名を生成する関数:
def sign_message(private_key, message: str, date: date):
    
    # メッセージに日付を追加 
    combined_message = message + str(date)
    
    # 署名を生成
    signature = private_key.sign(
        combined_message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

# 備考：crtファイルはuvicorn起動だけで使っているためここでは使わない。
#certificate = load_certificate("./my-local.crt")

#formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
#print(formatted_datetime)

# JWTの生成関数
def create_jwt(username: str, password: str):
    
    #formatted_datetime = str(datetime.today().strftime("%Y-%m-%d %H:%M"))
    #td = 60*60*24
    #timedelta(days= td * 60/td * 4)
    print("create_jwt payload前")
    payload = {
        "username": username,
        "password": password,
        "create-date": datetime.now(tz=timezone.utc).isoformat(),
        "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=15)
    }
    print("create_jwt payload後")
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# JWTの検証関数
def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print("Token is valid:", payload)
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        raise TokenExpiredException()
    except jwt.InvalidTokenError:
        print("Invalid token")
        raise NotAuthorizedException()


# Token期限切れ例外クラス
class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
# 認証不許可クラス
class NotAuthorizedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized")
