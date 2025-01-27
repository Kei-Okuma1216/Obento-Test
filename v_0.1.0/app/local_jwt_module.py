from functools import wraps
import logging
from pprint import pprint
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
# @log_decoratorを関数の上に記述すると、関数の前後にログを出力する
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

def get_now():
    return datetime.now(tz=timezone.utc)

# 有効期限操作
@log_decorator
async def get_token_limit(stage = None):
    if stage == 1:
        td = get_now() + timedelta(seconds=15)
    else:
        td = get_now() + timedelta(days=30)
    return td.isoformat()

# クッキーのexpに正確な日時をセット
def set_cookie_with_exp(response, userid, stage):
    exp = get_token_limit(stage)
    response.set_cookie(key="userid", value=userid, expires=exp)

@log_decorator
async def create_payload(username: str, password: str):
    cd = get_now().isoformat()
    exp = await get_token_limit(1)
    
    payload = {
        "username": username,
        "password": password,
        "create-date": cd,
        "exp": exp
    }
    pprint(payload)
    return payload

@log_decorator
async def create_jwt(payload):
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
