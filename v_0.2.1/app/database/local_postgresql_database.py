# database/local_postgresql_database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# postgreSQL用設定
from .settings import settings   # settings は .env から環境変数をロード
DATABASE_URL = settings.database_url


# 非同期エンジン作成
engine = create_async_engine(DATABASE_URL, echo=False) # echo=Trueでログを出力する

# セッションファクトリ
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Baseクラス（すべてのモデルの基底）
Base = declarative_base()

# データベースセッションを取得する関数
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 定数
ENDPOINT = settings.endpoint # "https://192.168.3.14:8000"
endpoint = ENDPOINT
default_shop_name = "shop01"
default_company_id = 1
default_compamy_name = "テンシステム"
default_menu_id = 1
default_amount = 1
