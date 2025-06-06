# tests/test_cancel_order.py

import pytest
from httpx import AsyncClient
from main import app  # ← FastAPIアプリが定義されているファイル
from sqlalchemy.ext.asyncio import AsyncSession
from models.order import Order  # SQLAlchemyモデル
from database import get_db  # 本番環境のget_db（後でオーバーライド）



# config/config_loader.py の load_permission_map() を変更

import os

def load_permission_map():
    path = os.environ.get("PERMISSION_MAP_PATH", "config/redirect_main_by_permission_map.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Permissionマップファイルが見つかりません: {path}")



# テスト用のDBやセッションを用意
# ここでは簡略化のためモックを使わずに、本物のテストDBとする前提（推奨）

@pytest.mark.asyncio
async def test_cancel_order_success(async_test_client: AsyncClient, test_session: AsyncSession):
    # 事前にキャンセル対象の注文データを追加
    test_order = Order(order_id=14, username="testuser", company_name="T社", shop_name="A店", menu_name="弁当", amount=1)
    test_session.add(test_order)
    await test_session.commit()

    # リクエスト用JSON
    payload = {
        "order_ids": [14],
        "user_id": 1  # ここは username へのマッピングが通る想定
    }

    # エンドポイントにPOST
    response = await async_test_client.post("/api/v1/order/cancel", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "キャンセル処理が完了しました"
    assert response.json()["canceled_order_ids"] == [14]
