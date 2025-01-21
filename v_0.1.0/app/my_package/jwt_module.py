from datetime import datetime, timedelta, timezone
import secrets
import jwt

SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"

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
