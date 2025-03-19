import os
import sys
import pytest
import asyncio
from fastapi.testclient import TestClient

# `app/` を `sys.path` に追加（Python に `app/` を認識させる）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app  # これで `main.py` を正しくインポートできる
# ← `main.py` から FastAPI アプリをインポート

import uvicorn

@pytest.fixture(scope="session", autouse=True)
def check_private_key():
    key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../my-local.key"))
    
    if not os.path.exists(key_path):
        pytest.exit(f"❌ my-local.key が見つかりません！パスを確認してください: {key_path}")
    
    print(f"✅ my-local.key が見つかりました: {key_path}")


@pytest.fixture(scope="module")
def test_app():
    # テスト用クライアントを作成
    client = TestClient(app)
    return client

@pytest.fixture(scope="module", autouse=True)
def run_server():
    """ テスト実行前にサーバーをバックグラウンドで起動 """
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    loop = asyncio.get_event_loop()
    task = loop.create_task(server.serve())
    
    yield  # テスト実行
    
    task.cancel()  # テスト後にサーバーを停止
