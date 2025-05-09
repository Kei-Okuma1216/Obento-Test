import pytest
from fastapi import HTTPException
from models.user import insert_new_user
from database._local_postgresql_database import override_get_db  # テストDBを使う場合

@pytest.mark.asyncio
async def test_insert_new_user_success():
    username = "test_user_1"
    password = "testpass"
    name = "Test Name"

    # 正常系の登録
    try:
        await insert_new_user(username, password, name)
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")

@pytest.mark.asyncio
async def test_insert_duplicate_user():
    username = "test_user_1"
    password = "testpass"
    name = "Test Name"

    # 同一ユーザー2回目の挿入でIntegrityErrorを期待
    with pytest.raises(HTTPException) as e:
        await insert_new_user(username, password, name)
    assert e.value.status_code == 400
    assert "すでに同じユーザー名が存在します" in e.value.detail
