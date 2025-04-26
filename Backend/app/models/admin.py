# models/admin.py
'''
    1. init_database():
    2. reset_all_autoincrement():
    3. drop_all_table():
    4. get_connection(): # sqlite用
    5. reset_all_autoincrement_and_drop_indexes_on_sqlite(): # sqlite用
    6. drop_all_table_on_sqlite(): # sqlite用
    7. drop_all_table():
    8. create_database(database_name: str = DATABASE_NAME):
    9. drop_database(database_name: str = DATABASE_NAME):
    10. create_all_tables_in_order():
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

from database.local_postgresql_database import engine, default_shop_name
'''------------------------------------------------------'''
from models.user import create_user_table, insert_shop, insert_user, update_existing_passwords, update_user
from models.company import create_company_table, insert_company
from models.menu import create_menu_table, insert_menu
from models.order import create_orders_table, insert_order

from core.settings import settings

@log_decorator
async def init_database():
    try:
        # テーブル削除
        db_name = settings.database_name

        await drop_database(db_name)  # データベースを削除
        # print(f"create_databse前まで {db_name=}")
        # return
        await create_database(db_name)
        await create_all_tables_in_order()

        # 会社情報の登録
        # 備考：Userの外部キーがcompaniesのため、先に登録する
        # await create_company_table()
        await insert_company("テンシステム", "083-999-9999", default_shop_name) # 1


        # ユーザー情報の登録
        # await create_user_table() 
        # 1
        await insert_user("user1", "user1", "大隈 慶1", company_id=1, shop_name=default_shop_name, menu_id=1) 
        # 2
        await insert_user("user2", "user2", "大隈 慶2", company_id=1, shop_name=default_shop_name, menu_id=1)
        # 3
        await insert_shop(default_shop_name, "shop01", "お店shop01")
        # 4
        await insert_user("manager", "manager", "manager", company_id=1, shop_name=default_shop_name, menu_id=1)
        await update_user("manager", "permission", 2) # ここで権限を変更する
        # 5
        await insert_user("admin", "admin", "admin", company_id=1, shop_name=default_shop_name, menu_id=1)


        await update_user("admin", "permission", 99)

        # 最後に全員のパスワードを暗号化する
        await update_existing_passwords() 



        # メニュー情報の登録
        # await create_menu_table()
        await insert_menu(
            shop_name=default_shop_name,
            name='お昼の定食',
            price=500,
            description='お昼のランチお弁当です',
            picture_path='/static/shops/1/menu/ランチ01.jpg') # 1


        # 注文情報の登録
        # await create_orders_table()
        
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

        logger.info("データベースファイル 'example' が正常に作成されました。")

    except (DatabaseError, SQLAlchemyError, IntegrityError, OperationalError) as e:
        raise
        # print(f"init_database - {str(e)}")       
        # logger.error(f"init_database - {str(e)}")
        # raise SQLException(
        #     sql_statement=str(stmt),
        #     method_name="init_database()",
        #     detail="SQL実行中にエラーが発生しました",
        #     exception=e
        # )
    except Exception as e: 
        print(f"init_database Error: {str(e)}")
        import traceback 
        traceback.print_exc()
        # raise CustomException(500, "init_database()", f"例外発生: {e}") from e

'''------------------------------------------------------'''
from core.settings import settings  # .envなどから読み込む設定ファイル

DATABASE_NAME = settings.database_name
DATABASE_URL = settings.database_url  # 通常は "postgres" DB への接続


# 注意：この関数は、PostgreSQLの管理DB（通常は "postgres"）に接続して実行する必要があります。
# 本番環境ではコメントアウトする
@log_decorator
async def drop_database(database_name: str = DATABASE_NAME):
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.sql import text

    # 重要：削除対象 DB にではなく、管理DB（postgres）に接続する
    ADMIN_DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/postgres"
    engine = create_async_engine(ADMIN_DATABASE_URL, echo=False)

    async with engine.connect() as raw_conn:
        # AUTOCOMMIT モードで操作する（非同期関数ではない）
        conn = await raw_conn.execution_options(isolation_level="AUTOCOMMIT")

        try:
            # データベースの存在確認
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database_name}
            )
            exists = result.scalar() is not None

            if exists:
                # 接続中の他セッションを強制切断
                await conn.execute(text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :dbname AND pid <> pg_backend_pid()
                """), {"dbname": database_name})

                # DROP DATABASE を実行
                await conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
                print(f"✅ Database '{database_name}' dropped successfully.")
            else:
                print(f"⚠️ Database '{database_name}' does not exist. Skipping drop.")

        except Exception as e:
            print(f"❌ An error occurred while dropping database '{database_name}': {e}")

    await engine.dispose()




from sqlalchemy import text
from database.local_postgresql_database import Base

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
        print(f"❌ An error occurred while dropping all tables: {e}")
        # raise CustomException(500, "drop_all_table()", f"Error: {e}") from e


# ------------------------------------------------------------------------------

# postgreSQL用設定
from core.settings import settings   # settings は .env から環境変数をロード
DATABASE_NAME = settings.database_name  # example
DATABASE_URL = settings.database_url

# 確認用関数
# SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :name AND pid <> pg_backend_pid();
# 使い方
# import asyncio
# asyncio.run(drop_database("your_test_db"))
@log_decorator
async def create_database(database_name: str = DATABASE_NAME):
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.sql import text

    # 管理DB（"postgres"）に接続
    ADMIN_DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/postgres"
    engine = create_async_engine(ADMIN_DATABASE_URL, echo=False)

    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")

        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": database_name}
        )
        exists = result.scalar() is not None

        if exists:
            print(f"⚠️ Database '{database_name}' already exists. Skipping creation.")
        else:
            try:
                await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
                print(f"✅ Database '{database_name}' created successfully.")
            except OperationalError as e:
                conn.rollback()
                print("データベース接続の問題:", e)
            except DatabaseError as e:
                print(f"❌ An error occurred while creating database '{database_name}': {e}")
                # raise SQLException(
                #     sql_statement=str(sqlstr),
                #     method_name="delete_all_company()",
                #     detail="SQL実行中にエラーが発生しました",
                #     exception=e
                # ) from e
            except Exception as e:
                print(f"❌ An error occurred while creating database '{database_name}': {e}")

    await engine.dispose()


from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DatabaseError
from utils.exception import CustomException

@log_decorator
async def create_all_tables_in_order():
    try:
        from models.company import Company
        from models.user import User
        from models.menu import Menu
        from models.order import Order

        # async with engine.begin() as conn:
            # テーブル作成順：依存関係のない順番に注意
            # await conn.run_sync(Company.__table__.create, checkfirst=True)
            # await conn.run_sync(User.__table__.create, checkfirst=True)
            # await conn.run_sync(Menu.__table__.create, checkfirst=True)
            # await conn.run_sync(Order.__table__.create, checkfirst=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ すべてのテーブル作成に成功しました。")

    except SQLAlchemyError as e:
        # SQLAlchemyエラー
        print(f"❌ テーブル作成中にSQLAlchemyエラーが発生しました: {e}")
        logger.error(f"SQLAlchemyエラー: create_all_tables_in_order() - {e}")
        # raise CustomException(500, "create_all_tables_in_order", f"SQLAlchemy error: {e}") from e
    except Exception as e:
        # その他の一般的なエラー
        print(f"❌ テーブル作成中に予期しないエラーが発生しました: {e}")
        # raise CustomException(500, "create_all_tables_in_order", f"Unexpected error: {e}") from e
