# # core/security.py
# # ここにauthなどかく


# メモ

# `core/security.py` は、アプリケーションの **認証・認可・暗号化・セキュリティ設定** を統一管理する重要なファイルです。特に
# **OAuth2、パスワード管理、トークン生成** などの処理を記述するのに適しています。

# ### `security.py` に書くべき内容:
# #### 1. パスワードのハッシュ化・検証
# ユーザーパスワードを安全に保存するために `bcrypt` や `passlib` を使用します。

# ```python
# from passlib.context import CryptContext

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def hash_password(password: str) -> str:
# return pwd_context.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
# return pwd_context.verify(plain_password, hashed_password)
# ```

# #### 2. JWT トークンの生成・検証
# OAuth2 で使用するアクセストークンを生成・検証する関数を記述します。

# ```python
# from datetime import datetime, timedelta
# from jose import JWTError, jwt

# SECRET_KEY = "your_secret_key"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# def create_access_token(data: dict, expires_delta: timedelta | None = None)
# -> str:
# to_encode = data.copy()
# expire = datetime.utcnow() + (expires_delta or
# timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
# to_encode.update({"exp": expire})
# return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def verify_token(token: str) -> dict | None:
# try:
# payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
# return payload
# except JWTError:
# return None
# ```

# #### 3. OAuth2 の認証フロー
# FastAPI の `OAuth2PasswordBearer` を利用し、API の認証プロセスを統一。

# ```python
# from fastapi.security import OAuth2PasswordBearer

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# ```

# #### 4. CSRF 保護
# セッションベースの認証を使う場合は **CSRF トークンの管理** も記述。

# ```python
# import secrets

# def generate_csrf_token() -> str:
# return secrets.token_urlsafe(32)
# ```

# #### 5. CORS 設定
# フロントエンドと連携する場合、安全な CORS 設定を `security.py` で一括管理。

# ```python
# from fastapi.middleware.cors import CORSMiddleware

# def setup_cors(app):
# app.add_middleware(
# CORSMiddleware,
# allow_origins=["https://yourfrontend.com"],
# allow_credentials=True,
# allow_methods=["*"],
# allow_headers=["*"],
# )
# ```

# ---

# ### `security.py` のメリット
# ✅ **一元管理** で可読性向上
# ✅ **拡張しやすい** (JWT / CSRF / CORS を一つのファイルで整理)
# ✅ **セキュリティの一貫性** を確保

# この構成なら、**OAuth2 や Cookie ベースの認証管理にも対応しやすい** ですね。
# 今の `bento order management app` の認証フローに合わせて、カスタマイズしたいポイントがあれば一緒に検討できますよ！
# [A](
# https://github.com/MaratBR/Telephonist/tree/7b900d7a6521082c1d84a935d70469b209782d57/server%2Fauth%2Fhash.py?copilot_analytics_metadata=eyJldmVudEluZm9fY29udmVyc2F0aW9uSWQiOiJoMm9MaVNzQU03UThLRG0xRVB3QnQiLCJldmVudEluZm9fbWVzc2FnZUlkIjoib0tDNVNyVzV1RDdSNUREZzF3QkxOIiwiZXZlbnRJbmZvX2NsaWNrRGVzdGluYXRpb24iOiJodHRwczpcL1wvZ2l0aHViLmNvbVwvTWFyYXRCUlwvVGVsZXBob25pc3RcL3RyZWVcLzdiOTAwZDdhNjUyMTA4MmMxZDg0YTkzNWQ3MDQ2OWIyMDk3ODJkNTdcL3NlcnZlciUyRmF1dGglMkZoYXNoLnB5IiwiZXZlbnRJbmZvX2NsaWNrU291cmNlIjoiY2l0YXRpb25MaW5rIn0%3D&citationMarker=9F742443-6C92-4C44-BF58-8F5A7C53B6F1)
# [B](
# https://github.com/Otters-Team-ugh-boger/api/tree/759deda150151bb19f9577d215b26ec4500f5920/api%2Fsecurity.py?copilot_analytics_metadata=eyJldmVudEluZm9fY29udmVyc2F0aW9uSWQiOiJoMm9MaVNzQU03UThLRG0xRVB3QnQiLCJldmVudEluZm9fY2xpY2tTb3VyY2UiOiJjaXRhdGlvbkxpbmsiLCJldmVudEluZm9fY2xpY2tEZXN0aW5hdGlvbiI6Imh0dHBzOlwvXC9naXRodWIuY29tXC9PdHRlcnMtVGVhbS11Z2gtYm9nZXJcL2FwaVwvdHJlZVwvNzU5ZGVkYTE1MDE1MWJiMTlmOTU3N2QyMTViMjZlYzQ1MDBmNTkyMFwvYXBpJTJGc2VjdXJpdHkucHkiLCJldmVudEluZm9fbWVzc2FnZUlkIjoib0tDNVNyVzV1RDdSNUREZzF3QkxOIn0%3D&citationMarker=9F742443-6C92-4C44-BF58-8F5A7C53B6F1
# )
