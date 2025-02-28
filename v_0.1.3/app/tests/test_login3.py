import pytest
import httpx
import asyncio
import subprocess
import time

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
        "cd /d C:\\Obento-Test\\v_0.1.2\\app & "
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
    '''
    # Uvicornのサーバをバックグラウンドで起動
    process = subprocess.Popen(["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"])
    '''
    '''
    server_process = subprocess.Popen(
        [
            "cmd.exe", "/c", "cd /d C:\\Obento-Test\\v_0.1.2\\app & .\\env\\Scripts\\activate & uvicorn main:app --host 127.0.0.1 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt"
        ],
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    '''
    # サーバが起動するのを少し待つ
    time.sleep(2)
    
    yield  # テスト実行
    
    # テスト完了後、サーバを停止
    time.sleep(15)
    process.terminate()
    process.wait()

# HTTPXを使った非同期ログインテスト
@pytest.mark.asyncio
async def test_login_success():
    async with httpx.AsyncClient(base_url="https://127.0.0.1:8000") as client:
        # ログインフォームにデータを送信
        response = await client.post("/login", data={"username": "user1", "password": "user1"})
        
        assert response.status_code == 200
        assert response.json()["message"] == "Login successful"

@pytest.mark.asyncio
async def test_login_failure():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post("/login", data={"username": "wronguser", "password": "wrongpassword"})
        
        assert response.status_code == 200
        assert response.json()["message"] == "Login failed"
