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
import asyncio
import logging
from venv import logger
logging.basicConfig(level=logging.INFO)

# 定数
from utils.utils import log_decorator, get_today_datetime
from core.constants import DEFAULT_COMPANY_NAME, DEFAULT_COMPANY_TEL, DEFAULT_SHOP_NAME, DEFAULT_LUNCH_NAME
from sqlalchemy.exc import DatabaseError

from database.local_postgresql_database import engine
'''------------------------------------------------------'''
from models.user import create_user_table, insert_shop, insert_user, update_existing_passwords, update_user
from models.company import create_company_table, insert_company
from models.menu import create_menu_table, insert_menu
from models.order import create_orders_table, insert_order

from core.settings import settings

@log_decorator
async def init_database():
    # 一度実行後は、コメントアウトしてください。
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
        
        # await insert_company("テンシステム", "083-999-9999", DEFAULT_SHOP_NAME) # 1
        await insert_company(DEFAULT_COMPANY_NAME, DEFAULT_COMPANY_TEL, DEFAULT_SHOP_NAME) # 1


        # ユーザー情報の登録
        # await create_user_table() 
        # 1
        await insert_user("user1", "user1", "大隈 慶1", company_id=1, shop_name=DEFAULT_SHOP_NAME, menu_id=1) 
        # 2
        await insert_user("user2", "user2", "大隈 慶2", company_id=1, shop_name=DEFAULT_SHOP_NAME, menu_id=1)
        # 3
        await insert_shop(DEFAULT_SHOP_NAME, "shop01", "お店shop01")
        # 4
        await insert_user("manager", "manager", "manager", company_id=1, shop_name=DEFAULT_SHOP_NAME, menu_id=1)
        await update_user("manager", "permission", 2) # ここで権限を変更する
        # 5
        await insert_user("admin", "admin", "admin", company_id=1, shop_name=DEFAULT_SHOP_NAME, menu_id=1)


        await update_user("admin", "permission", 99)

        # 最後に全員のパスワードを暗号化する
        await update_existing_passwords(request=None) 



        # メニュー情報の登録
        # await create_menu_table()
        await insert_menu(
            shop_name=DEFAULT_SHOP_NAME,
            name=DEFAULT_LUNCH_NAME,
            price=500,
            description='お昼のランチお弁当です',
            picture_path='/static/shops/1/menu/ランチ01.jpg') # 1


        # 注文情報の登録
        # await create_orders_table()
        
        # 1
        await insert_order(1, "user1", DEFAULT_SHOP_NAME, 1, 1, get_today_datetime(offset=-5))
        # 2
        await insert_order(1, "user2", DEFAULT_SHOP_NAME, 1, 2, get_today_datetime(offset=-4))
        # 3
        await insert_order(1, "tenten01", DEFAULT_SHOP_NAME, 1, 3, get_today_datetime(offset=-3))
        # 4
        await insert_order(1, "tenten02", DEFAULT_SHOP_NAME, 1, 1, get_today_datetime(offset=-2))
        # 5
        await insert_order(1, "user3", DEFAULT_SHOP_NAME, 1, 1, get_today_datetime(offset=-1))

        # 6
        await insert_order(1, "user1", DEFAULT_SHOP_NAME, 1, 1, get_today_datetime(offset=-1))
        # 7
        await insert_order(1, "user1", "shop02", 1, 1, get_today_datetime(offset=-1))

        # 本日の注文は挿入するとアプリテストできないのでコメントアウトした        
        # # 6
        # await insert_order(1, "user1", DEFAULT_SHOP_NAME, 1, 1)
        # # 7
        # await insert_order(1, "user1", "shop02", 1, 1)

        from datetime import datetime, timedelta
        tomorrow = get_today_datetime(offset=1)

        # 8
        # print(f"明日の日付: {tomorrow}")
        await insert_order(1, "user1", "shop01", 1, 1, tomorrow)

        # 9
        # print(f"明後日の日付: {tomorrow + timedelta(days=1)}")
        await insert_order(1, "user1", "shop01", 1, 1, tomorrow + timedelta(days=1))

        # 10
        # print(f"明後日の日付: {tomorrow + timedelta(days=2)}")
        await insert_order(1, "user1", "shop01", 1, 1, tomorrow + timedelta(days=2))

        # 11
        # print(f"明後日の日付: {tomorrow + timedelta(days=3)}")
        await insert_order(1, "user1", "shop01", 1, 1, tomorrow + timedelta(days=3))

        # 12
        # print(f"明後日の日付: {tomorrow + timedelta(days=4)}")
        await insert_order(1, "user1", "shop01", 1, 1, tomorrow + timedelta(days=4))

        # 13
        # print(f"明後日の日付: {tomorrow + timedelta(days=5)}")
        await insert_order(1, "user1", "shop01", 1, 1, tomorrow + timedelta(days=5))

        # 14
        # oneone = datetime(2025, 1, 1)
        # print(f"お正月の日付: {oneone}")
        await insert_order(1, "user1", "shop01", 1, 1, datetime(2025, 1, 1))

        logger.info("データベースファイル 'example' が正常に作成されました。")

    except (DatabaseError, SQLAlchemyError, IntegrityError, OperationalError) as e:
        logger.error(f"init_database Error: {str(e)}")
    except Exception as e: 
        logger.error(f"init_database Error: {str(e)}")

        import traceback 
        traceback.print_exc()

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
                logger.info(f"✅ Database '{database_name}' dropped successfully.")
            else:
                logger.info(f"⚠️ Database '{database_name}' does not exist. Skipping drop.")

        except Exception as e:
            logger.error(f"❌ An error occurred while dropping database '{database_name}': {e}")

    await engine.dispose()



from sqlalchemy import text
from sqlalchemy.exc import DatabaseError, SQLAlchemyError
from database.local_postgresql_database import Base
from fastapi import HTTPException

@log_decorator
async def drop_all_table():
    """
    Base.metadata に含まれる全テーブルを CASCADE オプション付きで削除します。
    テーブルごとに個別の例外処理を行い、エラーログを出力します。
    """
    try:
        async with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                sql_command = f'DROP TABLE IF EXISTS "public"."{table.name}" CASCADE'
                try:
                    print(f"{sql_command=}")
                    await conn.execute(text(sql_command))
                except DatabaseError as db_err:
                    logger.exception(f"DROP TABLE 失敗: {sql_command} - DBエラー: {db_err}")
                    # 失敗しても次のテーブル処理を続ける（必要なら return で停止可能）
                except Exception as ex:
                    logger.exception(f"DROP TABLE 失敗: {sql_command} - 予期せぬエラー: {ex}")
                    # 失敗しても次のテーブル処理を続ける（必要なら return で停止可能）

        logger.info("✅ 全テーブルのDrop処理が完了しました (CASCADE)")

    except SQLAlchemyError as e:
        logger.exception("全体処理中にSQLAlchemyのエラーが発生しました")
        raise HTTPException(
            status_code=500,
            detail="全テーブル削除中にデータベースエラーが発生しました。"
        )
    except Exception as e:
        logger.exception("全体処理中に予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=500,
            detail="全テーブル削除中にサーバー内部エラーが発生しました。"
        )
    else:
        logger.debug(f"DROP TABLE 成功: {sql_command}")

# from sqlalchemy import text
# from database.local_postgresql_database import Base

# @log_decorator
# async def drop_all_table():
#     """
#     SQLAlchemy の非同期エンジンを利用して、
#     Base.metadata に含まれる全テーブルを CASCADE オプション付きで削除します。
#     """
#     try:
#         async with engine.begin() as conn:
#             # sorted_tables は依存関係順になっているため、逆順に drop することで依存性を回避
#             for table in reversed(Base.metadata.sorted_tables):
#                 # テーブル名のみなら public スキーマの場合はそのままでOK。必要に応じてスキーマ指定を追加してください。
#                 # sql_command = f"DROP TABLE IF EXISTS {table.name} CASCADE"
#                 sql_command = f'DROP TABLE IF EXISTS "public"."{table.name}" CASCADE'
#                 print(f"{sql_command=}")
#                 #  スキーマ付きで明示的に DROP
#                 # sql_command = f'DROP TABLE IF EXISTS "public"."{table.name}" CASCADE'
#                 await conn.execute(text(sql_command))
#                 logger.debug(f"DROP TABLE: {sql_command}")
#         logger.debug("全テーブルのDrop完了 (CASCADE)")
#     except DatabaseError as e:
#         raise SQLException(
#             sql_statement=sql_command,
#             method_name="drop_all_table()",
#             detail="SQL実行中にエラーが発生しました",
#             exception=e
#         ) from e
#     except Exception as e:
#         print(f"❌ An error occurred while dropping all tables: {e}")
#         # raise CustomException(500, "drop_all_table()", f"Error: {e}") from e
#         logger.error(f"drop_all_table Error: {str(e)}")

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
    from core.settings import settings
    admin_db_url = settings.admin_database_url   
    engine = create_async_engine(admin_db_url, echo=False)

    # ADMIN_DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/postgres"
    # engine = create_async_engine(ADMIN_DATABASE_URL, echo=False)

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
                logger.info(f"✅ Database '{database_name}' created successfully.")
            except OperationalError as e:
                conn.rollback()
                print("データベース接続の問題:", e)
                logger.error(f"create_database Error: {str(e)}")
            except DatabaseError as e:
                print(f"❌ An error occurred while creating database '{database_name}': {e}")
                logger.error(f"create_database Error: {str(e)}")
            except Exception as e:
                print(f"❌ An error occurred while creating database '{database_name}': {e}")
                logger.error(f"create_database Error: {str(e)}")

    await engine.dispose()


from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DatabaseError

# @log_decorator
# async def create_all_tables_in_order(retry_count: int = 3, retry_delay: int = 2):
#     """
#     全テーブルを作成する。
#     - 失敗時はリトライする（最大retry_count回）
#     - リトライ間隔はretry_delay秒
#     """
#     attempt = 0
#     while attempt < retry_count:
#         try:
#             logger.info(f"🛠️ create_all_tables_in_order() - {attempt + 1}回目の試行")
#             print(f"🛠️ テーブル作成開始 ({attempt + 1}回目)")

#             async with engine.begin() as conn:
#                 await conn.run_sync(Base.metadata.create_all)

#             logger.info("✅ すべてのテーブル作成に成功しました。")
#             print("✅ すべてのテーブル作成に成功しました。")
#             return  # 成功したら抜ける

#         except (OperationalError, DatabaseError, SQLAlchemyError) as e:
#             attempt += 1
#             logger.error(f"❌ SQLAlchemyエラー (試行{attempt}回目): {e}")
#             print(f"❌ SQLAlchemyエラー発生 ({attempt}回目): {e}")

#             if attempt >= retry_count:
#                 logger.error(f"🛑 テーブル作成に{retry_count}回失敗しました。")
#                 print(f"🛑 テーブル作成に{retry_count}回失敗しました。")
#                 raise CustomException(500, "create_all_tables_in_order()", f"DBテーブル作成失敗: {e}")

#             logger.info(f"⏳ {retry_delay}秒後に再試行します...")
#             await asyncio.sleep(retry_delay)

#         except Exception as e:
#             logger.error(f"❌ 予期せぬエラー発生: {e}")
#             print(f"❌ 予期せぬエラー発生: {e}")
#             raise CustomException(500, "create_all_tables_in_order()", f"Unexpected error: {e}")

import inspect
import importlib
import pkgutil

@log_decorator
async def create_all_tables_in_order(retry_count: int = 3, retry_delay: int = 2):
    """
    modelsパッケージ内のすべてのテーブルを検出し、
    すでに存在するテーブルはスキップして、存在しないものだけ作成する。
    - 失敗時はリトライする（最大retry_count回）
    - リトライ間隔はretry_delay秒
    """
    attempt = 0
    while attempt < retry_count:
        try:
            logger.info(f"🛠️ create_all_tables_in_order() - {attempt + 1}回目の試行")
            print(f"🛠️ テーブル作成開始 ({attempt + 1}回目)")

            async with engine.begin() as conn:
                # modelsパッケージ内のすべてのモジュールを自動で読み込む
                import models
                for _, module_name, ispkg in pkgutil.iter_modules(models.__path__):
                    if not ispkg:
                        module = importlib.import_module(f"models.{module_name}")
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if hasattr(obj, "__table__"):
                                table_name = obj.__tablename__ if hasattr(obj, "__tablename__") else obj.__table__.name
                                logger.info(f"🔎 テーブル検出: {table_name}")
                                print(f"🔎 テーブル検出: {table_name}")
                                await conn.run_sync(lambda sync_conn: obj.__table__.create(sync_conn, checkfirst=True))
                                logger.info(f"✅ テーブル作成チェック完了: {table_name}")

            logger.info("✅ 必要なすべてのテーブル作成チェックが完了しました。")
            print("✅ 必要なすべてのテーブル作成チェックが完了しました。")
            return

        except (OperationalError, DatabaseError, SQLAlchemyError) as e:
            attempt += 1
            logger.error(f"❌ SQLAlchemyエラー (試行{attempt}回目): {e}")
            print(f"❌ SQLAlchemyエラー発生 ({attempt}回目): {e}")

            if attempt >= retry_count:
                logger.error(f"🛑 テーブル作成に{retry_count}回失敗しました。")
                print(f"🛑 テーブル作成に{retry_count}回失敗しました。")

            logger.info(f"⏳ {retry_delay}秒後に再試行します...")
            await asyncio.sleep(retry_delay)

        except Exception as e:
            logger.error(f"❌ 予期せぬエラー発生: {e}")
            print(f"❌ 予期せぬエラー発生: {e}")

        