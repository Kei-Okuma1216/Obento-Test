import pytest
import httpx
import ssl
import os

# 証明書の設定
#CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../app/my-local.crt"))
CERT_PATH = "C:/Obento-Test/v_0.1.3/app/my-local.crt"
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(CERT_PATH)
'''
[WinError 10048]
netstat -ano | findstr :8000
taskkill /PID 12345 /F
'''
# 証明書ファイルが存在するか確認
if os.path.exists(CERT_PATH):
    print("✅ 証明書が正しく存在します！")
else:
    print("❌ 証明書が見つかりません！パスを確認してください。")

# 証明書を `ssl_context` に適用（非推奨の `verify=str` を回避）
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(CERT_PATH)

@pytest.mark.asyncio
async def test_login_success():
    async with httpx.AsyncClient(base_url="https://127.0.0.1:8000", verify=ssl_context, follow_redirects=True) as client:

        # 1️⃣ Cookie なしで `/` にアクセス → `/login` にリダイレクトされるべき
        response = await client.get("/")
        assert response.status_code == 200  # `login.html` を受け取る

        # 2️⃣ `/login` に正しい認証情報を送信
        response = await client.post("/login", data={"username": "user1", "password": "user1"})
        assert response.status_code == 303  # リダイレクトが発生
        assert "set-cookie" in response.headers  # Cookie が設定されているか確認

        # 3️⃣ Cookie ありで `/` に再アクセス → `/order_complete` にリダイレクトされるべき
        response = await client.get("/")
        assert response.status_code == 200  # `order_complete.html` を受け取る

@pytest.mark.asyncio
async def test_login_failure():
    async with httpx.AsyncClient(base_url="https://127.0.0.1:8000", verify=ssl_context, follow_redirects=True) as client:

        # 1️⃣ `/login` に間違ったデータを送信
        response = await client.post("/login", data={"username": "wronguser", "password": "wrongpassword"})

        # 2️⃣ ログイン失敗時のレスポンスを確認
        assert response.status_code == 303  # `login.html` にリダイレクト
        assert "message=ログインに失敗しました" in response.headers["location"]  # リダイレクト URL にエラーメッセージが含まれる
