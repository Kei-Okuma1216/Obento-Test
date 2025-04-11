# database/sqlalchemy_database.py

from ast import stmt


from utils.exception import CustomException, SQLException
from utils.utils import log_decorator, get_today_str 

'''
    1. init_database():
    2. reset_all_autoincrement():
    3. drop_all_table():  
'''

# ログ用の設定
import logging
from venv import logger
logging.basicConfig(level=logging.INFO)

# 定数
db_name_str = "example.db"
#default_shop_name = "shop01"
from .sqlalchemy_database import engine, default_shop_name
'''------------------------------------------------------'''
from .user import create_user_table, insert_shop, insert_user, update_existing_passwords, update_user
from .company import create_company_table, insert_company
from .menu import create_menu_table, insert_menu
from .order import create_orders_table, insert_order

@log_decorator
async def init_database():
    try:
        # テーブル削除
        '''#await reset_all_autoincrement_on_sqlite()'''
        #await drop_all_table_on_sqlite()

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


        # 会社情報の登録
        await create_company_table()
        await insert_company("テンシステム", "083-999-9999", default_shop_name) # 1


        # メニュー情報の登録
        await create_menu_table()
        await insert_menu(shop_name=default_shop_name, name='お昼の定食', price=500, description='お昼のランチお弁当です', #picture_path='c:\\picture') # 1
        picture_path='/static/shops/1/menu/ランチ01.jpg') # 1


        # 注文情報の登録        
        await create_orders_table()
        # 1
        await insert_order(1, "user1", default_shop_name, 1, 1, get_today_str(-5))
        print(f"insert_order() - {get_today_str(-5)}")
        # 2
        await insert_order(1, "user2", default_shop_name, 1, 2, get_today_str(-4))
        print(f"insert_order() - {get_today_str(-4)}")
        # 3
        await insert_order(1, "tenten01", default_shop_name, 1, 3, get_today_str(-3))
        print(f"insert_order() - {get_today_str(-3)}")
        # 4
        await insert_order(1, "tenten02", default_shop_name, 1, 1, get_today_str(-2))
        print(f"insert_order() - {get_today_str(-2)}")
        # 5
        await insert_order(1, "user3", default_shop_name, 1, 1, get_today_str(-1))
        print(f"insert_order() - {get_today_str(-1)}")
        # 6
        await insert_order(1, "user1", "shop02", 1, 1, get_today_str())
        print(f"insert_order() - {get_today_str(-1)}")

        #await show_all_orders()

        logger.info("データベースファイル 'sample.db' が正常に作成されました。")

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="reset_all_autoincrement()",
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
from sqlalchemy.exc import DatabaseError
from .sqlalchemy_database import engine

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


'''------------------------------------------------------'''
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError
from .sqlalchemy_database import engine

@log_decorator
async def drop_all_table():
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
            method_name="drop_all_table()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "drop_all_table()", f"Error: {e}") from e


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
async def get_connection():
    try:
        return await aiosqlite.connect(DB_PATH, isolation_level=None, check_same_thread=False)

    except Exception as e:
        raise DatabaseConnectionException(
            method_name="get_connection()",
            detail="データベース接続に失敗しました。",
            exception=e
        )

# コネクションを閉じる（実際のテストでは不要）
#await conn.close()

@log_decorator
async def reset_all_autoincrement_and_drop_indexes_on_sqlite():
    """
    Orders, Companies, Menus, Users テーブルの自動採番用シーケンスをリセットし、
    それに関連するINDEXも削除する関数です。
    """
    conn = None
    try:
        conn = await get_connection()

        # AUTOINCREMENT のリセット
        for table in ["Companies", "Orders", "Menus", "Users"]:
            sqlstr = f'DELETE FROM sqlite_sequence WHERE name = "{table}"'
            await conn.execute(sqlstr)

        # INDEX の削除
        indexes = [
            "ix_companies_company_id",  # 会社IDに対するINDEX
            "ix_users_user_id",         # ユーザーIDに対するINDEX
            "ix_users_username"         # ユーザー名に対するUNIQUE INDEX
        ]
        for index in indexes:
            sqlstr_index = f"DROP INDEX IF EXISTS {index}"
            await conn.execute(sqlstr_index)

        await conn.commit()  # すべての変更をコミットする
        logger.debug("AUTOINCREMENTのリセットおよびINDEXの削除完了")

    except DatabaseConnectionException as e:
        raise
    except sqlite3.DatabaseError as e:
        raise SQLException(
            sql_statement=sqlstr,
            method_name="reset_all_autoincrement_and_drop_indexes_on_sqlite()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(
            500,
            "reset_all_autoincrement_and_drop_indexes_on_sqlite()",
            f"Error: {e}"
        ) from e
    finally:
        if conn is not None:
            await conn.close()


# 全テーブルをDrop
#@log_decorator
async def drop_all_table_on_sqlite():
    conn = None
    try:
        #'DROP TABLE IF EXISTS Company'
        conn = await get_connection()
        # AUTOINCREMENT のリセット
        for table in ["Company", "Orders", "Menu", "User"]:
            sqlstr = f'DROP TABLE IF EXISTS {table}'
            await conn.execute(sqlstr)

        await conn.commit()  # コミットを一度だけ実行
        logger.debug("全テーブルのDrop完了")
    except DatabaseConnectionException as e:
        raise
    except sqlite3.DatabaseError as e:
        raise SQLException(
            sql_statement=sqlstr,
            method_name="drop_all_table()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(
            500, f"drop_all_table()", f"Error: {e}")    
    finally:
        if conn is not None:
            await conn.close()

