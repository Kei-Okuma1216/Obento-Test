# database/local_postgresql_database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# postgreSQL用設定
from core.settings import settings   # settings は .env から環境変数をロード
DATABASE_NAME = settings.database_name
DATABASE_URL = settings.database_url
ENDPOINT = settings.endpoint # "https://192.168.3.14:8000"
endpoint = ENDPOINT

# 非同期エンジン作成
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,          # 最大接続数 (任意)
    max_overflow=20,       # 追加接続許容量 (任意)
    pool_timeout=30,       # 接続待機時間 (秒, 任意)
    pool_recycle=1800,     # 接続再作成時間 (秒, 30分)
    pool_pre_ping=True,    # 接続使用前に死活確認
    echo=False             # SQLログ出力を無効化
)

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

from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
import logging

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def create_session_with_retry():
    return AsyncSessionLocal()

'''
    try:
    async with get_db() as db:
        # データベース操作
        except ConnectionError as e:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "status_code": 500,
                "message": str(e)
            })
'''
@asynccontextmanager
async def get_db():
    try:
        session = await create_session_with_retry()
        try:
            yield session
        finally:
            await session.close()
    except RetryError as re:
        logger.error("データベース接続に3回失敗しました（タイムアウト）。AWS接続環境を確認してください。")
        raise ConnectionError("データベース接続に失敗しました。時間をおいて再試行してください。")

# 定数
default_shop_name = "shop01"
default_company_id = 1
default_compamy_name = "テンシステム"
default_menu_id = 1
default_amount = 1
