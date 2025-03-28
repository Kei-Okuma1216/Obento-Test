from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

print("database.py がインポートされました！")

DATABASE_URL = "sqlite+aiosqlite:///./example.db"

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
