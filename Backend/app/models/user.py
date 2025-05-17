# models/user.py
'''
    1. class UserModel(Base):
    2. create_user_table():

    3. select_user(username: str) -> Optional[UserModel]:
    4. select_user_by_id(user_id: int) -> Optional[UserResponse]:
    5. select_all_user() -> Optional[list[UserModel]]:

    6. get_hashed_password(password: str)-> str:
    7. update_existing_passwords():

    8. insert_user(username: str, password: str, name: str, company_id: int, shop_name: str, menu_id: int)-> bool:
    9. insert_new_user(username: str, password: str, name: str = '')-> bool:
    10. insert_shop(username: str, password: str, shop_name: str) -> None:

    11. update_user(username: str, key: str, value):
    12. delete_user(username: str):
    13. delete_all_user():
    14. execute_with_retry(session, stmt, retries=3, delay=1):
    15. get_user(username: str) -> Optional[UserResponse]:
    16. register_or_get_user(username: str, password: str, name: str) -> UserResponse:
'''
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, inspect, select, func
from database.local_postgresql_database import Base

# database.Userクラス
'''
    Userクラスは、SQLAlchemyのBaseクラスを継承しており、データベースのusersテーブルに対応しています。
'''
class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String(255))
    name = Column(String, nullable=True)
    token = Column(String, nullable=True)
    exp = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("Companies.company_id"))
    shop_name = Column(String, nullable=True)
    menu_id = Column(Integer, nullable=True)
    permission = Column(Integer, default=1)
    is_modified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())  # 作成日時(サーバー側作成日時)
    updated_at = Column(String, nullable=True)
    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    def get_id(self):
        return self.user_id
    def get_username(self):
        return self.username
    def get_password(self):
        return self.password
    def get_name(self):
        return self.name


# ログ用の設定
from log_unified import logger
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from utils.utils import log_decorator


from sqlalchemy.exc import DatabaseError, OperationalError ,IntegrityError
from database.local_postgresql_database import AsyncSessionLocal, default_shop_name, engine, get_db

# Userテーブル
# 作成
#@log_decorator
async def create_user_table():
    try:
        # AsyncEngineからbegin()を使用して接続を取得し、DDL操作を実行します。
        async with engine.begin() as conn:
            await conn.run_sync(User.__table__.create, checkfirst=True)
            logger.debug("User テーブルの作成（または既存）が完了しました。")
    except DatabaseError as e:
        engine.rollback()
        logger.error(f"create_user_table() でエラーが発生しました: {e}")
        raise


from sqlalchemy import select
from typing import Optional, List
from schemas.user_schemas import UserResponse
# 選択

@log_decorator
async def select_user(username: str) -> Optional[UserResponse]:
    try:
        sanitized_username = username.strip()
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.username == sanitized_username)
            logger.debug(f"select_user() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            orm_user = result.scalars().first()

            if orm_user is None:
                return None

            # ORMインスタンスの as_dict() メソッドを利用して辞書化する
            user_dict = orm_user.as_dict()
            logger.debug(f"user_dict: {user_dict}")

            # その辞書をもとに pydantic モデル UserResponse を生成
            user_model = UserResponse(**user_dict)
            logger.debug(f"user_model: {user_model}")

            return user_model

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")


@log_decorator
async def select_user_by_id(user_id: int) -> Optional[UserResponse]:
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.user_id == user_id)
            logger.debug(f"select_user_by_id() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            orm_user = result.scalars().first()

            if orm_user is None:
                return None

            # ORMインスタンスの as_dict() メソッドを利用して辞書化する
            user_dict = orm_user.as_dict()
            logger.debug(f"user_dict: {user_dict}")

            # その辞書をもとに pydantic モデル UserResponse を生成
            user_model = UserResponse(**user_dict)
            logger.debug(f"user_model: {user_model}")

            return user_model

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")




from .user import User  # ORMのUserモデル。適切なパスに合わせてください
from sqlalchemy import inspect


@log_decorator
async def select_all_users() -> Optional[List[UserResponse]]:
    """
    全てのUserレコードを取得し、pydanticのUserResponseのリストとして返します。
    (ユーザーが存在しない場合は None を返します)
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(User)
            logger.debug(f"select_all_users() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            # scalars() を使って ORM インスタンスを直接取得する
            orm_users = result.scalars().all()

            if not orm_users:
                logger.warning("No user found")
                return None

            user_models: List[UserResponse] = []
            for orm_user in orm_users:
                # inspect() を利用して各カラムの辞書を生成する
                inspector = inspect(orm_user)
                user_dict = {column.key: getattr(orm_user, column.key) for column in inspector.mapper.columns}
                # 得られた辞書データから UserResponse モデルを生成する
                user_model = UserResponse(**user_dict)
                user_models.append(user_model)

            return user_models

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")


import bcrypt
from fastapi import HTTPException, status

async def get_hashed_password(password: str) -> str:
    """パスワードをハッシュ化する（例外処理付き）"""
    try:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        new_hashed_password = hashed_password.decode()  # バイト列を文字列に変換

        logger.info("パスワードのハッシュ化に成功しました")
        return new_hashed_password

    except (ValueError, TypeError, UnicodeDecodeError) as e:
        logger.exception(f"パスワードのハッシュ化中にエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="パスワードのハッシュ化に失敗しました。"
        )
    except Exception as e:
        logger.exception("予期せぬエラーが発生しました（ハッシュ化）")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="内部エラーが発生しました。"
        )


from fastapi import Request
from pprint import pprint
"""新規登録したユーザーのパスワードをハッシュ化"""
@log_decorator
async def update_existing_passwords(request: Request):

    from utils.helper import redirect_login_success, redirect_error # これを設置して循環参照が起こるため関数内に移動した
    users = await select_all_users()  # すべてのユーザーを取得する関数が必要
    pprint(users)
    # セッションオブジェクトを非同期コンテキストマネージャで取得
    try:
        async with get_db() as session:

            for user in users:
                username = user.get_username()
                print(f"username: {username}")

                # 非同期セッションの場合、クエリの実行もawaitが必要となる
                result = await session.execute(select(User).filter_by(username=username))
                db_user = result.scalars().first()

                if db_user is None:
                    continue  # 該当ユーザーが存在しない場合はスキップ

                password = db_user.password  # 直接属性にアクセス可能
                print(f"password: {password}")

                if not password.startswith("$2b$"):  # bcryptのハッシュでない場合
                    """パスワードをハッシュ化する"""
                    salt = bcrypt.gensalt()
                    plain_password = user.get_password()
                    #password = user['password']
                    hashed_password = bcrypt.hashpw(plain_password.encode(), salt)
                    new_hashed_password = hashed_password.decode()

                    await update_user(
                        user.username, "password", new_hashed_password)

            message = f"ユーザー {user.username} のパスワードをハッシュ化しました"
            return redirect_login_success(request, message)

    except Exception as e:
        message = f"update_existing_passwords() - 予期せぬエラーが発生しました"
        return await redirect_error(request, message, e)


# 追加
''' 注意：データ新規作成後は、必ずデータベースのUserテーブルのパスワードを暗号化する
'''
@log_decorator
async def insert_user(
    username: str,
    password: str,
    name: str,
    company_id: int,
    shop_name: str,
    menu_id: int=1)-> bool:
    async with AsyncSessionLocal() as session:
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

            # return True

        except IntegrityError as e:
            await session.rollback()
            logger.exception(f"IntegrityError: {e}")
        except OperationalError as e:
            await session.rollback()
            logger.exception(f"OperationalError: {e}")
        except DatabaseError as e:
            await session.rollback()
            logger.exception(f"SQL実行中にエラーが発生しました:{e}")
        except Exception as e:
            await session.rollback()
            logger.exception(f"Unexpected error: {e}")
        else:
            logger.debug(f"insert_user() - ユーザー挿入: company_id: {company_id}, shop_name: {shop_name}, menu_id: {menu_id}")
            logger.info(f"ユーザー {username} の追加に成功しました。")

            return True

# デフォルト company_id を環境変数や設定ファイルで管理する
# DEFAULT_COMPANY_ID = 1
from core.constants import DEFAULT_COMPANY_ID
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from fastapi import HTTPException

# 新規ユーザー追加
from sqlalchemy import func
@log_decorator
async def insert_new_user(username: str, password: str, name: str = '') -> None:
    """
    新規ユーザーを登録する関数です。
    既に同じ username が存在する場合は挿入をスキップします。
    デフォルト値として、company_id=1, shop_name=default_shop_name, menu_id=1 が設定されます。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 既存ユーザーのチェック
            stmt = select(func.count()).select_from(User).where(User.username == username)
            count = await session.scalar(stmt)
            if count > 0:
                logger.debug(f"ユーザー {username} は既に存在します。挿入をスキップします。")
                return

            # パスワードのハッシュ化
            hashed_password = await get_hashed_password(password)

            # 新規ユーザーの作成（デフォルト値付き）
            new_user = User(
                username=username,
                password=hashed_password,
                name=name,
                token="",
                exp="",
                company_id=DEFAULT_COMPANY_ID,
                shop_name=default_shop_name,  # default_shop_name は適宜定義済みとします
                menu_id=1,
                permission=1  # 新規ユーザーのデフォルト権限（必要に応じて変更してください）
            )
            session.add(new_user)
            # print(".commit直前")
            await session.commit()

    except IntegrityError as e:
        logger.exception(f"ユーザー追加失敗: 一意制約違反または重複ユーザー - {e}")
        await session.rollback()  # セッションを復旧させる
        raise HTTPException(
            status_code=400,
            detail="すでに同じユーザー名が存在します。"
        )
    except OperationalError as e:
        logger.exception(f"DB操作中の接続エラー: {e}")
        await session.rollback()  # セッションを復旧させる        
        raise HTTPException(
            status_code=500,
            detail="データベース接続に失敗しました。"
        )
    except SQLAlchemyError as e:
        logger.exception(f"その他のDBエラー: {e}")
        await session.rollback()  # セッションを復旧させる
        raise HTTPException(
            status_code=500,
            detail="ユーザーの作成中にエラーが発生しました。"
        )
    except Exception as e:
        logger.exception(f"予期せぬエラー: {e}")
        await session.rollback()  # セッションを復旧させる
        raise HTTPException(
            status_code=500,
            detail="予期せぬエラーが発生しました。"
        )
    else:
        logger.info(f"ユーザー {username} の追加に成功しました。")
        logger.debug(
            f"insert_new_user() - 挿入実行: username: {username}, name: {name}, "
            f"company_id: {DEFAULT_COMPANY_ID}, shop_name: {default_shop_name}, menu_id: 1"
        )
        return True



# お弁当屋追加
# 備考：username == shop_name とする
from fastapi import Body

@log_decorator
async def insert_shop(
    username: str,
    password: str = Body(..., description="パスワードは平文"),
    shop_name: str = default_shop_name
) -> None:
    """
    店舗ユーザーを追加する関数です。
    既に指定の username が存在する場合は挿入をスキップします。
    備考：username == shop_name とする。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 既存のユーザー数をチェックする
            stmt = select(func.count()).select_from(User).where(User.username == username)
            count = await session.scalar(stmt)
            logger.debug(f"insert_shop() - ユーザー存在チェック: count = {count}")

            if count > 0:
                logger.debug(f"このユーザーID {username} は既に存在します。挿入をスキップします。")
                return

            # 新規ユーザーの作成（店舗ユーザーとして登録）
            new_user = User(
                username=username,
                password=password,
                name=shop_name,
                token="",
                exp="",
                company_id=1,
                shop_name=username,  # 備考：username == shop_name とする
                menu_id=1,
                permission=10
            )
            session.add(new_user)
            await session.commit()

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        logger.debug(
            f"insert_shop() - 挿入実行: username: {username}, name: {shop_name}, "
            f"shop_name: {username}, menu_id: 1, permission: 10"
        )
        logger.info("店舗ユーザー追加成功")


from sqlalchemy import update

@log_decorator
async def update_user(username: str, key: str, value):
    try:
        async with AsyncSessionLocal() as session:
            # 動的にカラム名を指定して更新するため、values() に辞書を利用
            stmt = update(User).where(User.username == username).values({key: value})
            await session.execute(stmt)
            await session.commit()

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        logger.info(f"ユーザー {username} の {key} を {value} に更新しました。")
        logger.debug(f"update_user() - {stmt}")


# 削除(1件)
from sqlalchemy import delete

@log_decorator
async def delete_user(username: str):
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(User).where(User.username == username)
            await session.execute(stmt)
            await session.commit()

            # return True

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        logger.info(f"ユーザー {username} の削除に成功しました。")
        logger.debug(f"delete_user() - {stmt}")


# 削除（全件）
from sqlalchemy import text
@log_decorator
async def delete_all_user():
    sqlstr = "DROP TABLE IF EXISTS users"

    def drop_table(sync_conn):
        sync_conn.execute(text(sqlstr))

    try:
        async with AsyncSessionLocal() as session:
            await session.run_sync(drop_table)

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        logger.info("User テーブルの削除が完了しました。")



import asyncio
async def execute_with_retry(session, stmt, retries=3, delay=1):
    """セッションとステートメントに対してリトライ付き実行"""
    for attempt in range(1, retries + 1):
        try:
            return await session.execute(stmt)
        except Exception as e:
            logger.warning(f"クエリ実行失敗 (試行 {attempt}/{retries}): {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                raise e

@log_decorator
async def get_user(username: str) -> Optional[UserResponse]:
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.username == username)
        result = await execute_with_retry(session, stmt)
        user_obj = result.scalar_one_or_none()

    if user_obj is None:
        return None

    return UserResponse(
        user_id=user_obj.user_id,
        username=user_obj.username,
        password=user_obj.password,
        name=user_obj.name,
        token=user_obj.token,
        exp=user_obj.exp,
        permission=user_obj.permission,
        company_id=user_obj.company_id,
        shop_name=user_obj.shop_name,
        menu_id=user_obj.menu_id,
        is_modified=user_obj.is_modified,
        updated_at=user_obj.updated_at
    )


@log_decorator
async def register_or_get_user(username: str, password: str, name: str) -> UserResponse:
    user = await get_user(username)
    if user:
        return user

    # ユーザーが存在しなければ新規作成
    await insert_new_user(username, password, name)

    # 作成後再取得
    user = await get_user(username)
    if user:
        return user

    logger.warning(f"ユーザー {username} の登録後取得に失敗しました")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="ユーザー登録後の取得に失敗しました。"
    )