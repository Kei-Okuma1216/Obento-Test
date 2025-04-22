# database/sqlalchemy_database.py
'''
    1. init_database():
    2. reset_all_autoincrement():
    3. drop_all_table():
    4. get_connection(): # sqlite用
    5. reset_all_autoincrement_and_drop_indexes_on_sqlite(): # sqlite用
    6. drop_all_table_on_sqlite(): # sqlite用
    7. drop_all_table():
    8. create_database(database_name: str = DATABASE_NAME):
'''

# ログ用の設定
import logging
from venv import logger
logging.basicConfig(level=logging.INFO)

# 定数
from ast import stmt
from utils.exception import CustomException, SQLException
from utils.utils import log_decorator, get_today_datetime
from sqlalchemy.exc import DatabaseError

# from .sqlalchemy_database import engine, default_shop_name
from database.local_postgresql_database import engine, default_shop_name
'''------------------------------------------------------'''
from .user import alter_orders_created_at_column_type, create_user_table, insert_shop, insert_user, update_existing_passwords, update_user
from .company import create_company_table, insert_company
from .menu import create_menu_table, insert_menu
from .order import create_orders_table, insert_order

from settings import settings

@log_decorator
async def init_database():
    try:
        # テーブル削除
        # await reset_all_autoincrement_on_sqlite()
        # await drop_all_table_on_sqlite()
        await drop_all_table()

        db_name = settings.database_name
        await create_database(db_name)

        # 会社情報の登録
        # 備考：Userの外部キーがcompaniesのため、先に登録する
        await create_company_table()
        await insert_company("テンシステム", "083-999-9999", default_shop_name) # 1


        # ユーザー情報の登録
        await create_user_table() 
        # 1
        await insert_user("user1", "user1", "大隈 慶1", company_id=1, shop_name=default_shop_name, menu_id=1) 
        # 2
        await insert_user("user2", "user2", "大隈 慶2", company_id=1, shop_name=default_shop_name, menu_id=1)
        # 3
        await insert_shop(default_shop_name, "shop01", "お店shop01")
        # 4
        await insert_user("manager", "manager", "manager", company_id=1, shop_name=default_shop_name, menu_id=1)
        await update_user("manager", "permission", 2)
        # 5
        await insert_user("admin", "admin", "admin", company_id=1, shop_name=default_shop_name, menu_id=1)


        await update_user("admin", "permission", 99)
        await update_existing_passwords() 


        # # 会社情報の登録
        # await create_company_table()
        # await insert_company("テンシステム", "083-999-9999", default_shop_name) # 1


        # メニュー情報の登録
        await create_menu_table()
        await insert_menu(shop_name=default_shop_name, name='お昼の定食', price=500, description='お昼のランチお弁当です', #picture_path='c:\\picture') # 1
        picture_path='/static/shops/1/menu/ランチ01.jpg') # 1


        # 注文情報の登録
        await create_orders_table()
        
        # await alter_orders_created_at_column_type()
        
        # 1
        await insert_order(1, "user1", default_shop_name, 1, 1, get_today_datetime(days_ago=5))
        # 2
        await insert_order(1, "user2", default_shop_name, 1, 2, get_today_datetime(days_ago=4))
        # 3
        await insert_order(1, "tenten01", default_shop_name, 1, 3, get_today_datetime(days_ago=3))
        # 4
        await insert_order(1, "tenten02", default_shop_name, 1, 1, get_today_datetime(days_ago=2))
        # 5
        await insert_order(1, "user3", default_shop_name, 1, 1, get_today_datetime(days_ago=1))
        # 6
        await insert_order(1, "user1", default_shop_name, 1, 1, get_today_datetime(days_ago=0))
        # 7
        await insert_order(1, "user1", "shop02", 1, 1, get_today_datetime(days_ago=0))

        logger.info("データベースファイル 'sample.db' が正常に作成されました。")

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="init_database()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e: 
        print(f"init_database Error: {str(e)}")
        #import traceback 
        #traceback.print_exc()
        raise CustomException(500, "init_database()", f"例外発生: {e}") from e

'''------------------------------------------------------'''
# AUTOINCREMENTフィールドをリセット
from sqlalchemy import text
# from .sqlalchemy_database import engine
from database.local_postgresql_database import engine

@log_decorator
async def reset_all_autoincrement():
    """
    Orders, Companies, Menus, Users テーブルの自動採番用シーケンスをリセットする関数です。
    各シーケンスを ALTER SEQUENCE ... RESTART WITH 1 によりリセットします。
    """
    try:
        async with engine.begin() as conn:
            sequences = [
                "orders_order_id_seq",      # Ordersテーブルのorder_id用シーケンス
                "companies_company_id_seq", # Companiesテーブルのcompany_id用シーケンス
                "menus_menu_id_seq",        # Menusテーブルのmenu_id用シーケンス
                "users_user_id_seq"         # Usersテーブルのuser_id用シーケンス
            ]
            for seq in sequences:
                stmt = text(f"ALTER SEQUENCE {seq} RESTART WITH 1")
                await conn.execute(stmt)
            logger.debug("各テーブルのシーケンス（自動採番）のリセット完了")
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="reset_all_autoincrement()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "reset_all_autoincrement()", f"Error: {e}") from e


# ------------------------------------------------------
from sqlalchemy import text
# from .sqlalchemy_database import engine
from database.local_postgresql_database import engine, Base


@log_decorator
async def drop_all_table_sqlite():
    """
    全テーブル（Companies、Orders、Menus、Users）を削除する関数です。
    SQLAlchemyの非同期エンジンを用いて各テーブルに対して
    'DROP TABLE IF EXISTS {table}' を実行します。
    """
    try:
        async with engine.begin() as conn:
            # 各テーブルに対してDROP文を実行
            for table in ["Companies", "Orders", "Menus", "Users"]:
                sqlstr = f"DROP TABLE IF EXISTS {table}"
                await conn.execute(text(sqlstr))
            logger.debug("全テーブルのDrop完了")
    except DatabaseError as e:
        raise SQLException(
            sql_statement=sqlstr,
            method_name="drop_all_table_sqlite()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "drop_all_table_sqlite()", f"Error: {e}") from e

# ------------------------------------------------------
from sqlalchemy import text
from database.order import Order
from database.company import Company
from database.menu import Menu
from database.user import User
from .local_postgresql_database import Base

@log_decorator
async def drop_all_table():
    """
    SQLAlchemy の非同期エンジンを利用して、
    Base.metadata に含まれる全テーブルを CASCADE オプション付きで削除します。
    """
    try:
        async with engine.begin() as conn:
            # sorted_tables は依存関係順になっているため、逆順に drop することで依存性を回避
            for table in reversed(Base.metadata.sorted_tables):
                # テーブル名のみなら public スキーマの場合はそのままでOK。必要に応じてスキーマ指定を追加してください。
                # sql_command = f"DROP TABLE IF EXISTS {table.name} CASCADE"
                sql_command = f'DROP TABLE IF EXISTS "public"."{table.name}" CASCADE'
                print(f"{sql_command=}")
                #  スキーマ付きで明示的に DROP
                # sql_command = f'DROP TABLE IF EXISTS "public"."{table.name}" CASCADE'
                await conn.execute(text(sql_command))
                logger.debug(f"DROP TABLE: {sql_command}")
        logger.debug("全テーブルのDrop完了 (CASCADE)")
    except DatabaseError as e:
        raise SQLException(
            sql_statement=sql_command,
            method_name="drop_all_table()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "drop_all_table()", f"Error: {e}") from e


# ------------------------------------------------------------------------------
from sqlalchemy.ext.asyncio import create_async_engine


# postgreSQL用設定
from .settings import settings   # settings は .env から環境変数をロード
DATABASE_NAME = settings.database_name  # example
DATABASE_URL = settings.database_url


from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

async def create_database(database_name: str = DATABASE_NAME):
    # 非同期エンジンを作成（管理用データベース "postgres" に接続）
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.connect() as conn:
        # トランザクション外で実行する必要があるため、AUTOCOMMITに設定
        await conn.execution_options(isolation_level="AUTOCOMMIT")

        # データベースの存在をチェック
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": database_name}
        )
        exists = result.scalar() is not None

        if exists:
            print(f"Database '{database_name}' already exists. Skipping creation.")
        else:
            try:
                await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
                print(f"Database '{database_name}' created successfully.")
            except Exception as e:
                print(f"An error occurred while creating database '{database_name}': {e}")

    await engine.dispose()


# # 非同期関数を実行する例
# if __name__ == "__main__":
#     asyncio.run(create_database("example"))
'''---------------------------------------------------------------'''
# sqlite用
import aiosqlite
import sqlite3
import os
from utils.exception import DatabaseConnectionException

# インメモリデータベースを作成
#conn = sqlite3.connect(':memory:')
db_name_str = "example.db"
default_shop_name = "shop01"

# データベース初期化
# プロジェクトルートからの絶対パスを取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 現在のファイルのディレクトリ
DB_PATH = os.path.join(BASE_DIR, db_name_str)  # sqlite_database.py と同じフォルダの sample.db を指定
#conn = sqlite3.connect(DB_PATH)

# コネクション取得
# async def get_connection():
#     try:
#         return await aiosqlite.connect(DB_PATH, isolation_level=None, check_same_thread=False)

#     except Exception as e:
#         raise DatabaseConnectionException(
#             method_name="get_connection()",
#             detail="データベース接続に失敗しました。",
#             exception=e
#         )

# コネクションを閉じる（実際のテストでは不要）
#await conn.close()

# @log_decorator
# async def reset_all_autoincrement_and_drop_indexes_on_sqlite():
#     """
#     Orders, Companies, Menus, Users テーブルの自動採番用シーケンスをリセットし、
#     それに関連するINDEXも削除する関数です。
#     """
#     conn = None
#     try:
#         conn = await get_connection()

#         # AUTOINCREMENT のリセット
#         for table in ["Companies", "Orders", "Menus", "Users"]:
#             sqlstr = f'DELETE FROM sqlite_sequence WHERE name = "{table}"'
#             await conn.execute(sqlstr)

#         # INDEX の削除
#         indexes = [
#             "ix_companies_company_id",  # 会社IDに対するINDEX
#             "ix_users_user_id",         # ユーザーIDに対するINDEX
#             "ix_users_username"         # ユーザー名に対するUNIQUE INDEX
#         ]
#         for index in indexes:
#             sqlstr_index = f"DROP INDEX IF EXISTS {index}"
#             await conn.execute(sqlstr_index)

#         await conn.commit()  # すべての変更をコミットする
#         logger.debug("AUTOINCREMENTのリセットおよびINDEXの削除完了")

#     except DatabaseConnectionException as e:
#         raise
#     except sqlite3.DatabaseError as e:
#         raise SQLException(
#             sql_statement=sqlstr,
#             method_name="reset_all_autoincrement_and_drop_indexes_on_sqlite()",
#             detail="SQL実行中にエラーが発生しました",
#             exception=e
#         )
#     except Exception as e:
#         raise CustomException(
#             500,
#             "reset_all_autoincrement_and_drop_indexes_on_sqlite()",
#             f"Error: {e}"
#         ) from e
#     finally:
#         if conn is not None:
#             await conn.close()


# # 全テーブルをDrop
# #@log_decorator
# async def drop_all_table_on_sqlite():
#     conn = None
#     try:
#         #'DROP TABLE IF EXISTS Company'
#         conn = await get_connection()
#         # AUTOINCREMENT のリセット
#         for table in ["Company", "Orders", "Menu", "User"]:
#             sqlstr = f'DROP TABLE IF EXISTS {table}'
#             await conn.execute(sqlstr)

#         await conn.commit()  # コミットを一度だけ実行
#         logger.debug("全テーブルのDrop完了")
#     except DatabaseConnectionException as e:
#         raise
#     except sqlite3.DatabaseError as e:
#         raise SQLException(
#             sql_statement=sqlstr,
#             method_name="drop_all_table()",
#             detail="SQL実行中にエラーが発生しました",
#             exception=e
#         )
#     except Exception as e:
#         raise CustomException(
#             500, f"drop_all_table()", f"Error: {e}")    
#     finally:
#         if conn is not None:
#             await conn.close()


