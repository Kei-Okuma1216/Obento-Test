# database/sqlalchemy_database.py
from datetime import date
import logging
from venv import logger


from utils.exception import CustomException, DatabaseConnectionException, SQLException
from utils.utils import log_decorator, get_today_str 

'''
    1. reset_all_autoincrement():
    2. drop_all_table():

    ここの関数は、modelsフォルダに移行した。    
'''

# ログ用の設定
logging.basicConfig(level=logging.INFO)

db_name_str = "example.db"
default_shop_name = "shop01"

# データベース初期化
# プロジェクトルートからの絶対パスを取得
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 現在のファイルのディレクトリ
DB_PATH = os.path.join(BASE_DIR, db_name_str)  # 

'''------------------------------------------------------'''

'''------------------------------------------------------'''

'''------------------------------------------------------'''

'''------------------------------------------------------'''
# AUTOINCREMENTフィールドをリセット
@log_decorator
async def reset_all_autoincrement():
    """
    Company, Menu, Ordersテーブルの自動採番用シーケンスをリセットする関数です。
    各シーケンスをALTER SEQUENCE ... RESTART WITH 1 によりリセットします。
    """
    try:
        async with engine.begin() as conn:
            sequences = [
                "company_company_id_seq",  # Companyテーブルのcompany_id用シーケンス
                "menu_menu_id_seq",        # Menuテーブルのmenu_id用シーケンス
                "orders_order_id_seq"      # Ordersテーブルのorder_id用シーケンス
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
        raise CustomException(500, "reset_all_autoincrement()", f"Error: {e}")


from sqlalchemy import engine, text
from sqlalchemy.exc import DatabaseError


@log_decorator
async def drop_all_table():
    """
    全テーブル（Company、Orders、Menu、User）を削除する関数です。
    SQLAlchemyの非同期エンジンを用いて各テーブルに対して
    'DROP TABLE IF EXISTS {table}' を実行します。
    """
    try:
        async with engine.begin() as conn:
            # 各テーブルに対してDROP文を実行
            for table in ["Company", "Orders", "Menu", "User"]:
                sqlstr = f"DROP TABLE IF EXISTS {table}"
                await conn.execute(text(sqlstr))
            logger.debug("全テーブルのDrop完了")
    except DatabaseError as e:
        raise SQLException(
            sql_statement=sqlstr,
            method_name="drop_all_table()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "drop_all_table()", f"Error: {e}")


'''------------------------------------------------------'''

from user import user # user.pyからインポート

'''------------------------------------------------------'''
#@log_decorator
async def init_database():
    default_shop_name = "shop01"
    try:
        await reset_all_autoincrement()
        await drop_all_table()

        await create_user_table() 
        # 1
        await insert_user("user1", "user1", "大隈 慶1", company_id=1, shop_name=default_shop_name, menu_id=1) 
        # 2
        await insert_user("user2", "user2", "大隈 慶2", company_id=1, shop_name=default_shop_name, menu_id=1)
        # 3
        await insert_shop(default_shop_name, default_shop_name, "お店shop01")
        # 4
        await insert_user("manager", "manager", "manager", company_id=1, shop_name=default_shop_name, menu_id=1)
        await update_user("manager", "permission", 2)
        # 5
        await insert_user("admin", "admin", "admin", company_id=1, shop_name=default_shop_name, menu_id=1)
        await update_user("admin", "permission", 99)

        #from routers.admin import update_existing_passwords
        await update_existing_passwords() 

        await create_company_table()
        await insert_company("テンシステム", "083-999-9999", "shop01") # 1

        await create_menu_table()

        await insert_menu(shop_name='shop01', name='お昼の定食', price=500, description='お昼のランチお弁当です', #picture_path='c:\\picture') # 1
        picture_path='/static/shops/1/menu/ランチ01.jpg') # 1
        
        await create_orders_table()
        '''INSERT INTO Orders (company_id, username, shop_name, menu_id,  amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)'''
        
        
        # 1
        await insert_order(1, "user1", "shop01", 1, 1, get_today_str(-5))
        print(f"insert_order() - {get_today_str(-5)}")
        # 2
        await insert_order(1, "user2", "shop01", 1, 2, get_today_str(-4))
        print(f"insert_order() - {get_today_str(-4)}")
        # 3
        await insert_order(1, "tenten01", "shop01", 1, 3, get_today_str(-3))
        print(f"insert_order() - {get_today_str(-3)}")
        # 4
        await insert_order(1, "tenten02", "shop01", 1, 1, get_today_str(-2))
        print(f"insert_order() - {get_today_str(-2)}")
        # 5
        await insert_order(1, "user3", "shop01", 1, 1, get_today_str(-1))
        print(f"insert_order() - {get_today_str(-1)}")
        # 6
        await insert_order(1, "user1", "shop02", 1, 1, get_today_str())
        print(f"insert_order() - {get_today_str(-1)}")
        
        await show_all_orders()

        logger.info("データベースファイル 'sample.db' が正常に作成されました。")

    except DatabaseConnectionException as e:
        raise
    except sqlite3.Error as e: 
        raise
    except Exception as e: 
        print(f"init_database Error: {str(e)}")
        import traceback 
        traceback.print_exc()
        raise CustomException(
            500, "init_database()", f"例外発生: {e}")

