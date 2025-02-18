from functools import wraps
from pprint import pprint
from typing import Union
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from datetime import date, datetime, timedelta, timezone
import jwt
import os
from utils import JST, get_max_age, get_now, log_decorator

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY", "3a5e8e2b7c9d5f7b6a1b2e9f8e2d6c3e4f5a6b7c8d9e0a1b2c3d4e5f6a7b8c9d")
TOKEN_EXPIRE_MINUTES = 15
TOKEN_EXPIRE_DAYS = 30

# ログ用の設定
#logging.basicConfig(level=logging.INFO)



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

@log_decorator
def get_new_token(data) -> str:
    try:
        expires_delta_15s = timedelta(seconds=15)
        expires_delta_30s = timedelta(seconds=30)
        expires_delta_30m = timedelta(minutes=30)
        expires_delta_1d = timedelta(days=1)
        expires_delta_30d = timedelta(days=30)
        #expires_delta = expires_delta_30d
        #if not expires_delta:
        #    raise HTTPException(status_code=404,
        #                        detail="expires delta undefined")

        expired_time = get_now(JST) + expires_delta_30d
        print(f"expired_time: {expired_time}")
        print("ここまできた 1")
        # UNIX時間に変換
        unix_time = get_max_age(expired_time)
        #int(expired_time.timestamp())   
        print(f"unix_time: {unix_time}")
        
        to_encode = data.copy()
        print("ここまできた 2")
        
        username = data['sub']
        permission = data['permission']
        
        to_encode.update({"sub": username})
        to_encode.update({"permission": permission})
        to_encode.update({"max-age": unix_time})
        
        pprint(to_encode)
        print("ここまできた 3")
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, 
                                 algorithm=ALGORITHM)
        print("ここまできた 4")
        return encoded_jwt, unix_time
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
# cookieのtoken有無と有効期限をチェックする
@log_decorator
def check_cookie_token(request):
    token = request.cookies.get("token")
    if token is None: 
        print(f"クッキーに token がありません")
        return None
        #return redirect_login(request, "tokenの有効期限が切れています。再登録をしてください。")
        # その返り値を返していません。
        #そのため、関数はその後も処理を続け、最終的に token, max_age を返してしまいます。
    else:
        print(f"token: あり")
        print(f"token: {token}")
        
    max_age = request.cookies.get("max-age")    
    if max_age is None:
        print("クッキーに max-age がありません")
        return None
        #return redirect_login(request, "tokenの有効期限が切れています。再登録をしてください。")
    else:
        print(f"max_age: {max_age}")

    print(f"end of check_cookie_token()")
    print(f"max_age: {max_age}")
    return token ,max_age

# Token期限切れ例外クラス
class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
# 認証不許可クラス
class NotAuthorizedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized")

# JWTトークンの生成
@log_decorator
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# JWTトークンのデコード
@log_decorator
def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
