import ssl
import pytest
import httpx
import asyncio
import subprocess
import time
import logging

import os

# 証明書設定
#CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../app/my-local.crt"))
CERT_PATH = "C:/Obento-Test/v_0.1.3/app/my-local.crt"
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(CERT_PATH)

# 証明書ファイルが存在するか確認
if os.path.exists(CERT_PATH):
    print("✅ 証明書が正しく存在します！")
else:
    print("❌ 証明書が見つかりません！パスを確認してください。")
'''
[WinError 10048]
netstat -ano | findstr :8000
taskkill /PID 12345 /F
'''
# ログ設定
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# テストサーバを起動するヘルパー関数
@pytest.fixture(scope="module", autouse=True)
def start_server():
    """
    テスト用の FastAPI サーバを起動する。
    - Windows のコマンドプロンプトで仮想環境を有効化
    - SSL 証明書を適用
    - uvicorn を起動
    """
    # 実行コマンド（Windows用・SSL対応）
    command = [
        "cmd.exe", "/c",
        "cd /d C:\\Obento-Test\\v_0.1.3\\app & "
        ".\\env\\Scripts\\activate & "
        "uvicorn main:app --host 127.0.0.1 --port 8000 "
        "--ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt"
    ]
    # 新しいコンソールウィンドウでサーバーを起動
    process = subprocess.Popen(
        command,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    # サーバが起動するのを少し待つ
    time.sleep(5)
    print("テスト開始")
    yield  # テスト実行
    
    # テスト完了後、サーバを停止
    time.sleep(5)
    process.terminate()
    process.wait()

# HTTPXを使った非同期ログインテスト
@pytest.mark.asyncio
async def test_login_success():
    async with httpx.AsyncClient(base_url="https://127.0.0.1:8000", 
    verify=CERT_PATH) as client:
        # まず / に GET でアクセス（ログインページにリダイレクト）
        response = await client.get("/")
        assert response.status_code in [200, 307, 308]  # 307, 308 はリダイレクト

        #verify="./my-local.pem") as client:
        # ログインフォームにデータを送信
        logger.debug(f"client: {client}")
        logger.info("# ログインフォームに正常なデータを送信")
        #print(f"client: {client}")
        #print(f"# ログインフォームに正常なデータを送信")
        response = await client.post("/", data={"username": "user1", "password": "user1"})
        
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        # SUCCESS 200, METHOD NOT ALLOWED 405
        assert response.status_code == 200
        assert response.json()["message"] == "Login successful"

@pytest.mark.asyncio
async def test_login_failure():
    async with httpx.AsyncClient(base_url="https://127.0.0.1:8000", verify=CERT_PATH) as client:
        print(f"# ログインフォームに間違ったデータを送信")
        response = await client.post("/login", data={"username": "wronguser", "password": "wrongpassword"})
        
        assert response.status_code == 200
        assert response.json()["message"] == "Login failed"
