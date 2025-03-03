import pytest
from httpx import AsyncClient
from main import app  # FastAPIアプリ
import ssl

# SSL設定（テスト環境用）
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


@pytest.mark.asyncio
async def test_custom_exception():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/test_exception")  # 例外が発生するエンドポイント

        # 1️⃣ ステータスコードのチェック
        assert response.status_code == 400  # `CustomException(400, "これはテストエラーです")` の通り

        # 2️⃣ レスポンスのHTMLテンプレートをチェック
        assert "これはテストエラーです" in response.text  # error.html でエラーメッセージが表示されているか
