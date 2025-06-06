# tests/conftest.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.local_postgresql_database import get_db
# from database.local_postgresql_database import Base
from app.main import app

import os

os.environ["PERMISSION_MAP_PATH"] = "tests/test_data/mock_permission_map.json"


DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/example"

# テスト用DB接続
test_engine = create_async_engine(DATABASE_URL, echo=True)
TestSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

@pytest.fixture(scope="function")
async def test_session():
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
async def async_test_client(test_session):
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="https://192.168.3.14:8000") as client:
        yield client

# 実行時に一時的にパスを通してください。
# PowerShell (一時的にパスを通す例)
## $env:PYTHONPATH = ".."
# $env:PERMISSION_MAP_PATH = "tests/test_data/mock_permission_map.json"
# pytest -v

# cd ..
# pytest -v tests/
