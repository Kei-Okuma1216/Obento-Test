# models/user.py
'''
    class User(Base):
    create_user_table():
    select_user(username: str) -> Optional[User]:
    select_all_user() -> Optional[list[User]]:
    insert_user(username, password, name, company_id, shop_name, menu_id):
    insert_new_user(username: str, password: str, name: str = ''):
    update_user(username: str, key: str, value):
    delete_user(username: str):

    get_hashed_password(password: str):
'''
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, select, func
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# models.Userクラス
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String(255))
    name = Column(String, nullable=True)
    token = Column(String, nullable=True)
    exp = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=True)
    shop_name = Column(String, nullable=True)
    menu_id = Column(Integer, nullable=True)
    permission = Column(Integer, default=1)
    is_modified = Column(Boolean, default=False)
    updated_at = Column(String, nullable=True)
    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


import logging
logger = logging.getLogger(__name__)


from utils.exception import CustomException, SQLException, DatabaseConnectionException
from utils.utils import log_decorator

from database import engine  # AsyncEngine インスタンスが定義されている前提

# Userテーブル
# 作成
@log_decorator
async def create_user_table():
    try:
        async with engine.begin() as conn:
            # User.__table__.create を run_sync() で呼び出す（checkfirst=True で存在チェック）
            await conn.run_sync(User.__table__.create, checkfirst=True)
            logger.debug("User テーブルの作成（または既存）が完了しました。")
    except Exception as e:
        logger.error(f"create_user_table() でエラーが発生しました: {e}")
        raise

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_session
from typing import Optional

# 選択
@log_decorator
async def select_user(username: str) -> Optional[User]:
    try:
        sanitized_username = username.strip()

        async with async_session() as session:
            stmt = select(User).where(User.username == sanitized_username)
            result = await session.execute(stmt)
            user = result.scalars().first()
            logger.debug(f"select_user() - SQLAlchemyクエリ: {stmt}")
            return user
    except Exception as e:
        raise CustomException(500, "select_user()", f"Error: {e}") from e


# 選択（全件）
@log_decorator
async def select_all_user() -> Optional[list[User]]:
    """
    全てのUserレコードを取得する
    """
    try:
        async with async_session() as session:
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            logger.debug(f"select_all_user() - SQLAlchemyクエリ: {stmt}")
            return users

    except Exception as e:
        raise CustomException(500, "select_all_user()", f"Error: {e}") from e


from sqlalchemy.exc import DatabaseError

# 追加
@log_decorator
async def insert_user(username, password, name, company_id, shop_name, menu_id):
    async with async_session() as session:
        try:
            # ユーザーが既に存在するか確認
            stmt = select(func.count()).select_from(User).where(User.username == username)
            result = await session.execute(stmt)
            count = result.scalar()
            logger.debug(f"insert_user() - COUNTクエリ - count: {count}")

            if count > 0:
                logger.info(f"ユーザーID: {username} は既に存在します。挿入をスキップします。")
                return False

            # パスワードのハッシュ化
            hashed_password = await get_hashed_password(password)

            # 新規ユーザーの作成
            new_user = User(
                username=username,
                password=hashed_password,
                name=name,
                token='',
                exp='',
                company_id=company_id,
                shop_name=shop_name,
                menu_id=menu_id
            )
            session.add(new_user)
            await session.commit()

            logger.info("ユーザー追加成功")
            logger.debug(f"insert_user() - ユーザー挿入: company_id: {company_id}, shop_name: {shop_name}, menu_id: {menu_id}")
            return True

        except DatabaseConnectionException as e:
            raise
        except DatabaseError as e:
            raise SQLException(
                sql_statement="UserのINSERT処理",
                method_name="insert_user()",
                detail="SQL実行中にエラーが発生しました",
                exception=e
            )
        except Exception as e:
            raise CustomException("UserのINSERT処理", f"insert_user() Error: {e}")


from utils.utils import default_shop_name

# 新規ユーザー追加
@log_decorator
async def insert_new_user(username: str, password: str, name: str = ''):
    try:
        # insert_userはSQLAlchemyの非同期ORMを利用した関数（前回実装例参照）
        result = await insert_user(
            username,
            password,
            name,
            company_id=1,
            shop_name=default_shop_name,
            menu_id=1
        )
        return result
    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(500, "insert_new_user()", f"Error: {e}")

from sqlalchemy import update

@log_decorator
async def update_user(username: str, key: str, value):
    try:
        async with async_session() as session:
            # 動的にカラム名を指定して更新するため、values() に辞書を利用
            stmt = update(User).where(User.username == username).values({key: value})
            await session.execute(stmt)
            await session.commit()
            logger.debug(f"update_user() - {stmt}")

    except DatabaseConnectionException as e:
        raise
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="update_users()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "update_user()", f"Error: {e}")

from sqlalchemy import delete

# 削除
@log_decorator
async def delete_user(username: str):
    try:
        async with async_session() as session:
            stmt = delete(User).where(User.username == username)
            await session.execute(stmt)
            await session.commit()
            logger.info(f"ユーザー {username} の削除に成功しました。")
            logger.debug(f"delete_user() - {stmt}")
            return True

    except DatabaseConnectionException as e:
        raise
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="delete_user()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "delete_user()", f"Error: {e}")


import bcrypt

# パスワードをハッシュ化
@log_decorator
async def get_hashed_password(password: str):
    """パスワードをハッシュ化する"""
    # bcryptは同期的なライブラリですが、ここでは非同期関数内でそのまま利用しています
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    new_hashed_password = hashed_password.decode()  # バイト列を文字列に変換
    print(f"new_hashed_password: {new_hashed_password}")
    return new_hashed_password