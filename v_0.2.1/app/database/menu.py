# models/menu.py
'''
    1. class Menu(Base):
    2. create_menu_table():

    3. select_menu(shop_name: str, -> Optional[Menu]:
    4. select_all_menu(shop_name: str, menu_id: int=1) -> Optional[list[Menu]]:

    5. insert_menu(shop_name: str, name: str, price: int, description: str = "", picture_path: str = "", disabled: bool = False) -> bool:
    6. update_menu(shop_name: str, menu_id: int, key: str, value: str) -> int:
    7. delete_menu(shop_name: str, menu_id: int) -> int:
    8. delete_all_menus():
'''
from datetime import datetime
from sqlalchemy import Text
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from .sqlalchemy_database import Base, AsyncSessionLocal
from sqlalchemy.exc import DatabaseError

from utils.exception import CustomException, SQLException
from utils.utils import log_decorator

'''------------------------------------------------------'''
# Menuテーブル
class Menu(Base):
    __tablename__ = "menus"

    menu_id = Column(Integer, primary_key=True, autoincrement=True)
    shop_name = Column(String, nullable=True)  # 店舗名
    name = Column(String, nullable=False)  # メニュー名
    price = Column(Integer, nullable=False)  # 価格
    description = Column(Text, default="")  # 説明（デフォルト空）
    picture_path = Column(String, default="")  # 画像パス（デフォルト空）
    disabled = Column(Boolean, default=False)  # 0: 利用可能, 1: 利用不可
    created_at = Column(DateTime, default=datetime.utcnow)  # 作成日時

    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

import logging
logger = logging.getLogger(__name__)

'''------------------------------------------------------'''
from .sqlalchemy_database import engine
# 作成
@log_decorator
async def create_menu_table():
    """
    Menuテーブルを作成する（既に存在する場合は作成されません）。
    """
    try:
        # AsyncEngineからbegin()を使用して接続を取得し、DDL操作を実行します。
        async with engine.begin() as conn:
            await conn.run_sync(Menu.__table__.create, checkfirst=True)
            logger.debug("create_menu_table() - Menuテーブルの作成に成功しました。")

    except DatabaseError as e:
        raise SQLException(
            sql_statement="CREATE TABLE menu",
            method_name="create_menu_table()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "create_menu_table()", f"Error: {e}")

'''------------------------------------------------------'''
from typing import Optional
from sqlalchemy import select

from .user import User # ここを修正する。
from .menu import Menu

# 選択
@log_decorator
async def select_menu(shop_name: str, menu_id: int = 1) -> Optional[Menu]:
    """
    指定された shop_name と menu_id の条件に合致する、ある店舗が持つ特定の Menu レコードを取得する。
    存在しなければ None を返す。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Menu)
                .join(User, Menu.shop_name == User.shop_name)
                .where(
                    User.shop_name == shop_name,
                    Menu.menu_id == menu_id
                )
            )
            logger.debug(f"select_menu() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            menu = result.scalars().first()
            return menu

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_menu()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_menu()", f"Error: {e}")



from typing import List, Optional

@log_decorator
async def select_all_menus(shop_name: str) -> Optional[List[Menu]]:
    """
    UserテーブルとMenuテーブルを内部結合し、指定された shop_name に該当する Menuレコードを全件取得する。
    戻り値は Menu オブジェクトのリストとして返す（該当レコードがなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Menu)
                .join(User, Menu.shop_name == User.shop_name)
                .where(User.shop_name == shop_name)
            )
            logger.debug(f"select_all_menus() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            menus = result.scalars().all()
            if not menus:
                logger.warning(f"No menu found for shop_name: {shop_name}")
                return None
            return menus

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_all_menus()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_all_menus()", f"Error: {e}")


'''------------------------------------------------------'''
from sqlalchemy import func  # COUNT用

@log_decorator
async def insert_menu(
    shop_name: str,
    menu_name: str,
    price: int,
    description: str = "",
    picture_path: str = "",
    disabled: bool = False
) -> bool:
    """
    指定された shop_name に対応する店舗に対して、Menu レコードを挿入する関数です。
    同じ店舗（shop_name）で同じメニュー名 (name) のレコードが存在するかを SELECT COUNT(*) でチェックします。
    存在すれば挿入をスキップして False を返し、存在しなければ INSERT を実行して True を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 重複チェック：同じ店舗（shop_name）で同じメニュー名 (name) があるかをCOUNTする
            count_stmt = select(func.count(Menu.menu_id)).where(
                Menu.shop_name == shop_name,
                Menu.name == menu_name
            )
            count_result = await session.execute(count_stmt)
            count = count_result.scalar()  # COUNT の結果を取得
            logger.debug(f"insert_menu() - Duplicate check count: {count}")

            if count > 0:
                logger.info(f"Menu '{menu_name}' for shop '{shop_name}' already exists. Insertion skipped.")
                return False

            # 重複がなければ、新規 Menu レコードを作成・追加する
            new_menu = Menu(
                shop_name=shop_name,
                name=menu_name,
                price=price,
                description=description,
                picture_path=picture_path,
                disabled=disabled
            )
            session.add(new_menu)
            await session.commit()
            logger.info(f"Menu '{menu_name}' for shop '{shop_name}' inserted successfully.")
            return True

    except DatabaseError as e:
        raise SQLException(
            sql_statement="insert_menu()",
            method_name="insert_menu()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException("insert_menu()", f"Error: {e}")


'''------------------------------------------------------'''
from sqlalchemy import update

# 更新
@log_decorator
async def update_menu(shop_name: str, menu_id: int, key: str, value: str) -> int:
    """
    指定された shop_name と menu_id に一致する Menu レコードの指定カラムを更新する。
    更新に成功したレコード数（通常は1）を返す。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 動的カラム名を安全に扱うために getattr を使用
            column_attr = getattr(Menu, key, None)
            if column_attr is None:
                raise CustomException(400, "update_menu()", f"不正なカラム名です: {key}")

            stmt = (
                update(Menu)
                .where(Menu.menu_id == menu_id, Menu.shop_name == shop_name)
                .values({column_attr: value})
            )

            result = await session.execute(stmt)
            await session.commit()

            updated_count = result.rowcount
            logger.info(f"メニュー更新成功（更新件数: {updated_count}）")
            logger.debug(f"update_menu() - SQL: {stmt}, key: {key}, value: {value}")

            return updated_count

    except DatabaseError as e:
        raise SQLException(
            sql_statement=f"UPDATE Menu SET {key} = {value} WHERE menu_id = {menu_id} AND shop_name = {shop_name}",
            method_name="update_menu()",
            detail=f"SQLAlchemy 実行中にエラーが発生しました: {e}",
            exception=e
        )
    except CustomException:
        raise
    except Exception as e:
        raise CustomException(500, "update_menu()", f"Error: {e}")


'''------------------------------------------------------'''
from sqlalchemy import delete

# 削除(1件)
@log_decorator
async def delete_menu(shop_name: str, menu_id: int) -> int:
    """
    指定された shop_name と menu_id に一致する Menu レコードを削除する。
    削除件数（通常は1）を返す。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                delete(Menu)
                .where(Menu.menu_id == menu_id, Menu.shop_name == shop_name)
            )

            result = await session.execute(stmt)
            await session.commit()

            deleted_count = result.rowcount
            logger.info(f"メニュー削除成功（削除件数: {deleted_count}）")
            logger.debug(f"delete_menu() - SQL: {stmt}")

            return deleted_count

    except DatabaseError as e:
        raise SQLException(
            sql_statement=f"DELETE FROM menu WHERE shop_name = {shop_name} AND menu_id = {menu_id}",
            method_name="delete_menu()",
            detail=f"SQLAlchemy 実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "delete_menu()", f"Error: {e}")


from sqlalchemy import text
# 全削除
@log_decorator
async def delete_all_menu():
    sqlstr = "DROP TABLE IF EXISTS menu"
    try:
        def drop_table(sync_conn):
            sync_conn.execute(text(sqlstr))

        async with AsyncSessionLocal() as session:
            await session.run_sync(drop_table)
            logger.info("Menu テーブルの削除が完了しました。")

    except DatabaseError as e:
        raise SQLException(
            sql_statement=sqlstr,
            method_name="delete_all_menu()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "delete_all_menu()", f"Error: {e}")

