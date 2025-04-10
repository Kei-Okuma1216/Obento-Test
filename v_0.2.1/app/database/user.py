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
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, select, func
#default_shop_name = "shop01"
from sqlalchemy.exc import DatabaseError
from .sqlalchemy_database import Base, AsyncSessionLocal, default_shop_name

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


# ログ用の設定
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from utils.exception import CustomException, SQLException
from utils.utils import log_decorator

#default_shop_name = "shop01"

from .sqlalchemy_database import engine
# Userテーブル
# 作成
@log_decorator
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

# 選択
@log_decorator
async def select_user(username: str) -> Optional[UserModel]:
    try:
        sanitized_username = username.strip()

        async with AsyncSessionLocal() as session:
            stmt = select(User).where(UserModel.username == sanitized_username)
            print(f"**ここまでOK 1 execute前 stmt: {stmt}")
            result = await session.execute(stmt)
            print(f"**ここまでOK 2")
            user = result.scalars().first()
            logger.debug(f"select_user() - SQLAlchemyクエリ: {stmt}")

            return user

    except DatabaseError as e:
        raise CustomException(500, "select_user()", f"Error: {e}") from e


# 選択（全件）
@log_decorator
async def select_all_users() -> Optional[list[UserModel]]:
    """
    全てのUserレコードを取得する
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(UserModel)
            result = await session.execute(stmt)
            users = result.scalars().all()
            logger.debug(f"select_all_user() - SQLAlchemyクエリ: {stmt}")
            return users

    except DatabaseError as e:
        raise CustomException(500, "select_all_user()", f"Error: {e}") from e



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


# パスワードをハッシュ化する関数
#@log_decorator
async def update_existing_passwords():
    """既存ユーザーのパスワードをハッシュ化"""
    users = await select_all_users()  # すべてのユーザーを取得する関数が必要
    for user in users:
        if not user['password'].startswith("$2b$"):  # bcryptのハッシュでない場合
        #if not user.get_password().startswith("$2b$"):  # bcryptのハッシュでない場合

            """パスワードをハッシュ化する"""
            salt = bcrypt.gensalt()
            #password = user.get_password()
            password = user['password']
            hashed_password = bcrypt.hashpw(password.encode(), salt)
            new_hashed_password = hashed_password.decode()  # バイト列を文字列に変換
            #new_hashed_password = hash_password(user.get_password())  # ハッシュ化

            await update_user(
                user.username, "password", new_hashed_password)  # DB更新
            logger.info(f"ユーザー {user.username} のパスワードをハッシュ化しました")




# 追加
''' 注意：データ新規作成後は、必ずデータベースのUserテーブルのパスワードを暗号化する
'''
@log_decorator
async def insert_user(username: str, password: str, name: str, company_id: int, shop_name: str, menu_id: int)-> bool:
    async with AsyncSessionLocal() as session:
        try:
            # ユーザーが既に存在するか確認
            stmt = select(func.count()).select_from(UserModel).where(UserModel.username == username)
            result = await session.execute(stmt)
            count = result.scalar()
            logger.debug(f"insert_user() - COUNTクエリ - count: {count}")

            if count > 0:
                logger.info(f"ユーザーID: {username} は既に存在します。挿入をスキップします。")
                return False

            # パスワードのハッシュ化
            hashed_password = await get_hashed_password(password)

            # 新規ユーザーの作成
            new_user = UserModel(
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
            )
        except Exception as e:
            raise CustomException("UserのINSERT処理", f"insert_user() Error: {e}")


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
            stmt = select(func.count()).select_from(UserModel).where(UserModel.username == username)
            count = await session.scalar(stmt)
            #logger.debug(f"insert_new_user() - ユーザー存在チェック: count = {count}")

            if count > 0:
                logger.debug(f"ユーザー {username} は既に存在します。挿入をスキップします。")
                return

            # 新規ユーザーの作成（デフォルト値付き）
            new_user = UserModel(
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
        )
    except Exception as e:
        raise CustomException(500, "insert_new_user()", f"Error: {e}")


# お弁当屋追加
# 備考：username == shop_name とする
from sqlalchemy import select, func
from sqlalchemy.exc import DatabaseError

@log_decorator
async def insert_shop(username: str, password: str, shop_name: str) -> None:
    """
    店舗ユーザーを追加する関数です。
    既に指定の username が存在する場合は挿入をスキップします。
    備考：username == shop_name とする。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 既存のユーザー数をチェックする
            stmt = select(func.count()).select_from(UserModel).where(UserModel.username == username)
            count = await session.scalar(stmt)
            logger.debug(f"insert_shop() - ユーザー存在チェック: count = {count}")

            if count > 0:
                logger.debug(f"このユーザーID {username} は既に存在します。挿入をスキップします。")
                return

            # 新規ユーザーの作成（店舗ユーザーとして登録）
            new_user = UserModel(
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
        )
    except Exception as e:
        raise CustomException(500, "insert_shop()", f"Error: {e}")



from sqlalchemy import update

@log_decorator
async def update_user(username: str, key: str, value):
    try:
        async with AsyncSessionLocal() as session:
            # 動的にカラム名を指定して更新するため、values() に辞書を利用
            stmt = update(UserModel).where(UserModel.username == username).values({key: value})
            await session.execute(stmt)
            await session.commit()
            logger.debug(f"update_user() - {stmt}")

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="update_users()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except DatabaseError as e:
        raise CustomException(500, "update_user()", f"Error: {e}")

# 削除(1件)
from sqlalchemy import delete

@log_decorator
async def delete_user(username: str):
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(UserModel).where(UserModel.username == username)
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
        )
    except DatabaseError as e:
        raise CustomException(500, "delete_user()", f"Error: {e}")

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
        )
    except Exception as e:
        raise CustomException(500, "delete_all_user()", f"Error: {e}")




