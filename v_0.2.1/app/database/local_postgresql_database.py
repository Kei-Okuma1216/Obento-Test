# database/local_postgresql_database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite+aiosqlite:///./example.db"

db_name_str = "example.db"

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 現在のファイルの絶対パスを取得
DB_PATH = os.path.join(BASE_DIR, db_name_str)  # 

# 非同期エンジン作成
engine = create_async_engine(DATABASE_URL, echo=True)

# セッションファクトリ
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Baseクラス（すべてのモデルの基底）
Base = declarative_base()

# データベースセッションを取得する関数
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

endpoint = "https://192.168.3.19:8000"

default_shop_name = "shop01"
default_company_id = 1
default_compamy_name = "テンシステム"
default_menu_id = 1
default_amount = 1
'''メモ
PostgreSQL や MySQL なら asyncpg.exceptions.PostgresError や aiomysql.Error などをキャッチすべきです。
しかしasyncpg.exceptions.PostgresError や aiomysql.Error は、SQLAlchemy のエンジンを使用している場合は、SQLAlchemy の例外にラップされているため、直接キャッチする必要はありません。
SQLAlchemy の例外は、SQLAlchemy のドキュメントに記載されています。
'''

