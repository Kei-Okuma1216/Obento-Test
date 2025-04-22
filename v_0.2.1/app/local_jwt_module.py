from fastapi import HTTPException, status
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from datetime import date, datetime, timedelta, timezone
import jwt
import os
from utils.utils import log_decorator

SECRET_KEY = os.getenv("SECRET_KEY", "3a5e8e2b7c9d5f7b6a1b2e9f8e2d6c3e4f5a6b7c8d9e0a1b2c3d4e5f6a7b8c9d")
ALGORITHM = "HS256"

# TOKEN_EXPIRE_MINUTES = 15

CERT_FILE = "app/keys/my-local.crt"
KEY_FILE = "app/keys/my-local.key"

# ログ用の設定
#logging.basicConfig(level=logging.INFO)

# 秘密鍵my-local.keyをファイルから読む
def load_private_key(key_file: str):
    key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), key_file))  # 絶対パスに変換
    with open(key_path, "rb") as key_file:
        return key_file.read()
'''
# 秘密鍵my-local.keyをファイルから読む
def load_private_key(key_file: str): 
    with open(key_file, "rb") as key_file:
        private_key = load_pem_private_key(key_file.read(), password=None) 
        return private_key 
'''

private_key = load_private_key("./my-local.key")
#private_key = load_private_key(KEY_FILE)


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


# TODO：ここはアクセストークン取得ラッパーをつくる
# 有効期限を第二引数にセットする
TOKEN_EXPIRE_DAYS = 30

@log_decorator
def get_access_token(data) -> str:
    access_token = get_new_token(data)
    return access_token

@log_decorator
def get_new_token(data) -> str:
    ''' トークンの有効期限はutc日付で表す
    '''
    try:
        to_encode = data.copy()

        to_encode.update({"sub": data['sub']})
        to_encode.update({"permission": data['permission']})

        expired_time = datetime.now() + timedelta(days=TOKEN_EXPIRE_DAYS)
        expired_time_utc = expired_time.astimezone(timezone.utc)

        # ISO形式の文字列に変換
        expires = expired_time_utc.isoformat().replace('+00:00', 'Z')
        # 更新
        to_encode.update({"expires": expires})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, 
                                 algorithm=ALGORITHM)
        return encoded_jwt, expires
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
'''
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
'''