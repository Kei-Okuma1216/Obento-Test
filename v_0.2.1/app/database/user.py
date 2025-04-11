# database/user.py
'''
    1. class UserModel(Base):
    2. create_user_table():

    3. select_user(username: str) -> Optional[UserModel]:
    4. select_all_user() -> Optional[list[UserModel]]:

    5. get_hashed_password(password: str)-> str:
    6. update_existing_passwords():

    7. insert_user(username: str, password: str, name: str, company_id: int, shop_name: str, menu_id: int)-> bool:
    8. insert_new_user(username: str, password: str, name: str = '')-> bool:
    9. insert_shop(username: str, password: str, shop_name: str) -> None:

    10. update_user(username: str, key: str, value):
    11. delete_user(username: str):
    12. delete_all_user():
'''
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, inspect, select, func
#default_shop_name = "shop01"
from .sqlalchemy_database import Base, AsyncSessionLocal, default_shop_name, get_db
# database.Userクラス
'''
    Userクラスは、SQLAlchemyのBaseクラスを継承しており、データベースのusersテーブルに対応しています。
'''
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
    def get_username(self):
        return self.username
    def get_password(self):
        return self.password


# ログ用の設定
from log_config import logger
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from sqlalchemy.exc import DatabaseError
from .sqlalchemy_database import Base, AsyncSessionLocal, default_shop_name, get_db

from utils.exception import CustomException, SQLException
from utils.utils import log_decorator



from .sqlalchemy_database import engine
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
        logger.error(f"create_user_table() でエラーが発生しました: {e}")
        raise


from sqlalchemy import select
from typing import Optional
from schemas.user_schemas import UserResponse
# 選択
from database.user import AsyncSessionLocal  # 適切なパスに合わせてください


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
            print(f"user_model: {user_model}")

            return user_model

    except DatabaseError as e:
        raise CustomException(500, "select_user()", f"Error: {e}") from e
    except Exception as e:
        raise CustomException(500, "select_user()", f"Error: {e}") from e



from sqlalchemy import select
from sqlalchemy.exc import DatabaseError
from typing import Optional, List
from schemas.user_schemas import UserResponse
from database.user import AsyncSessionLocal  # 適宜パスを調整してください
from utils.exception import CustomException
from utils.utils import log_decorator
from log_config import logger

from sqlalchemy import select
from sqlalchemy.exc import DatabaseError
from typing import Optional, List
from schemas.user_schemas import UserResponse
from database.user import AsyncSessionLocal  # 適宜パスを調整してください
from .user import User  # ORMのUserモデル。適切なパスに合わせてください
from utils.exception import CustomException
from utils.utils import log_decorator
from log_config import logger

from sqlalchemy import select, inspect
from sqlalchemy.exc import DatabaseError
from typing import Optional, List
from schemas.user_schemas import UserResponse
from database.user import AsyncSessionLocal  # 必要に応じてパスを調整してください
#from models.user import User  # ORMのUserモデル。適宜パスを調整してください
from utils.exception import CustomException
from utils.utils import log_decorator
from log_config import logger

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

    except DatabaseError as e:
        raise CustomException(500, "select_all_users()", f"Error: {e}") from e
    except Exception as e:
        raise CustomException(500, "select_all_users()", f"Error: {e}") from e






import bcrypt

# パスワードをハッシュ化
#@log_decorator
async def get_hashed_password(password: str)-> str:
    """パスワードをハッシュ化する"""
    # bcryptは同期的なライブラリですが、ここでは非同期関数内でそのまま利用しています
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    new_hashed_password = hashed_password.decode()  # バイト列を文字列に変換
    print(f"new_hashed_password: {new_hashed_password}")

    return new_hashed_password


"""既存ユーザーのパスワードをハッシュ化"""
#@log_decorator
async def update_existing_passwords():

    users = await select_all_users()  # すべてのユーザーを取得する関数が必要

    # セッションオブジェクトを非同期コンテキストマネージャで取得
    async with get_db() as session:
        for user in users:
            username = user.get_username()
            # 非同期セッションの場合、クエリの実行もawaitが必要となる
            result = await session.execute(select(User).filter_by(username=username))
            db_user = result.scalars().first()
            if db_user is None:
                continue  # 該当ユーザーが存在しない場合はスキップ

        password = db_user.password  # 直接属性にアクセス可能
        print(f"password: {password}")

        if not password.startswith("$2b$"):  # bcryptのハッシュでない場合
        #if not user.get_password().startswith("$2b$"):  # bcryptのハッシュでない場合

            """パスワードをハッシュ化する"""
            salt = bcrypt.gensalt()
            password = user.get_password()
            #password = user['password']
            hashed_password = bcrypt.hashpw(password.encode(), salt)
            new_hashed_password = hashed_password.decode()

            await update_user(
                user.username, "password", new_hashed_password)

            logger.info(f"ユーザー {user.username} のパスワードをハッシュ化しました")


# 追加
''' 注意：データ新規作成後は、必ずデータベースのUserテーブルのパスワードを暗号化する
'''
@log_decorator
async def insert_user(
    username: str, password: str, name: str,
    company_id: int, shop_name: str, menu_id: int=1)-> bool:
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

            logger.info("ユーザー追加成功")
            logger.debug(f"insert_user() - ユーザー挿入: company_id: {company_id}, shop_name: {shop_name}, menu_id: {menu_id}")
            return True

        except DatabaseError as e:
            raise SQLException(
                sql_statement="UserのINSERT処理",
                method_name="insert_user()",
                detail="SQL実行中にエラーが発生しました",
                exception=e
            ) from e
        except Exception as e:
            raise CustomException("UserのINSERT処理", f"insert_user()", f"Error: {e}") from e


# 新規ユーザー追加
from sqlalchemy import select, func
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
            #logger.debug(f"insert_new_user() - ユーザー存在チェック: count = {count}")

            if count > 0:
                logger.debug(f"ユーザー {username} は既に存在します。挿入をスキップします。")
                return

            # 新規ユーザーの作成（デフォルト値付き）
            new_user = User(
                username=username,
                password=password,
                name=name,
                token="",
                exp="",
                company_id=1,
                shop_name=default_shop_name,  # default_shop_name は適宜定義済みとします
                menu_id=1,
                permission=1  # 新規ユーザーのデフォルト権限（必要に応じて変更してください）
            )
            session.add(new_user)
            await session.commit()
            logger.info("新規ユーザー登録成功")

    except DatabaseError as e:
        raise SQLException(
            sql_statement="INSERT INTO users ...",  # 実際のSQL文は省略
            method_name="insert_new_user()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "insert_new_user()", f"Error: {e}") from e


# お弁当屋追加
# 備考：username == shop_name とする
from sqlalchemy import select, func
from sqlalchemy.exc import DatabaseError

@log_decorator
async def insert_shop(
    username: str, password: str, shop_name: str) -> None:
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
            logger.debug(
                f"insert_shop() - 挿入実行: username: {username}, name: {shop_name}, "
                f"shop_name: {username}, menu_id: 1, permission: 10"
            )
            logger.info("店舗ユーザー追加成功")

    except DatabaseError as e:
        raise SQLException(
            sql_statement="INSERT INTO users ...",  # 詳細なSQL文は省略
            method_name="insert_shop()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "insert_shop()", f"Error: {e}") from e



from sqlalchemy import update

@log_decorator
async def update_user(username: str, key: str, value):
    try:
        async with AsyncSessionLocal() as session:
            # 動的にカラム名を指定して更新するため、values() に辞書を利用
            stmt = update(User).where(User.username == username).values({key: value})
            await session.execute(stmt)
            await session.commit()
            logger.debug(f"update_user() - {stmt}")

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="update_users()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except DatabaseError as e:
        raise CustomException(500, "update_user()", f"Error: {e}") from e

# 削除(1件)
from sqlalchemy import delete

@log_decorator
async def delete_user(username: str):
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(User).where(User.username == username)
            await session.execute(stmt)
            await session.commit()
            logger.info(f"ユーザー {username} の削除に成功しました。")
            logger.debug(f"delete_user() - {stmt}")
            return True

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="delete_user()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except DatabaseError as e:
        raise CustomException(500, "delete_user()", f"Error: {e}") from e

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
            logger.info("User テーブルの削除が完了しました。")
    except DatabaseError as e:
        raise SQLException(
            sql_statement=sqlstr,
            method_name="delete_all_user()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "delete_all_user()", f"Error: {e}") from e




