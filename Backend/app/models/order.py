# models/orders.py
'''
    注文クエリ関数

    1. class Orders(Base):
    2. create_orders_table():

    # 管理者(admin)用に注文を取得する
    3. select_single_order(order_id: int) -> OrderModel:
    4. select_all_orders() -> Optional[List[OrderModel]]:

    # 一般ユーザー(username) を指定して、注文を取得する
    5. select_orders_by_user_all(username: str) -> Optional[List[OrderModel]]:
    6. select_orders_by_user_at_date(username: str, target_date: date) -> Optional[List[OrderModel]]:
    7. select_orders_by_user_ago(username: str, days_ago: int = 0) -> Optional[List[OrderModel]]:

    # 契約企業(company_id) を指定して、注文を取得する
    8. select_orders_by_company_all(company_id: int) -> Optional[List[OrderModel]]:
    9. select_orders_by_company_at_date(company_id: int, target_date: date) -> Optional[List[OrderModel]]:
    10. select_orders_by_company_ago(company_id: int, days_ago_str: str = None) -> Optional[List[OrderModel]]:

    # 店舗(shop_name) を指定して、注文を取得する
    11. all(shop_name: str) -> Optional[List[OrderModel]]:
    12. select_orders_by_shop_company(shop_name: str, company_id: int) -> Optional[List[OrderModel]]:
    13. select_orders_by_shop_at_date(shop_name: str, target_date: date) -> Optional[List[OrderModel]]:
    14. select_orders_by_shop_ago(shop_name: str, days_ago_str: str) -> Optional[List[OrderModel]]:

    15. insert_order(company_id: int, username: str, shop_name: str, menu_id: int, amount: int, created_at: Optional[str] = None) -> int:
    16. update_order(order_id: int, company_id: int, username: str, shop_name: str, menu_id: int, amount: int, updated_at: Optional[str] = None) -> bool:
    17. delete_order(order_id: int) -> bool:
    18. delete_all_orders():
'''
from sqlalchemy import Column, Integer, String, DateTime
from database.local_postgresql_database import Base, engine

# SELECT * FROM public."Orders"
# ORDER BY order_id DESC

class Order(Base):
    __tablename__ = "Orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer)
    username = Column(String)
    shop_name = Column(String)
    menu_id = Column(Integer)
    amount = Column(Integer)
    created_at = Column(DateTime) # このままでOK
    # created_at = Column(DateTime, server_default=func.now())  # 作成日時(サーバー側作成日時)
    updated_at = Column(DateTime) # このままでOK
    # created_at = Column(PG_TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    # updated_at = Column(PG_TIMESTAMP(timezone=True), onupdate=func.now())
    canceled = Column(Integer, default=0)

    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


from utils.exception import CustomException, SQLException
from utils.utils import get_today_datetime, log_decorator


import logging
logger = logging.getLogger(__name__)
from log_unified import logger, order_logger

from sqlalchemy.exc import DatabaseError


# 作成
@log_decorator
async def create_orders_table():
    """
    Ordersテーブルを作成する（存在しなければ作成）
    """
    try:
        # AsyncEngineからbegin()を使用して接続を取得し、DDL操作を実行します。
        async with engine.begin() as conn:
            await conn.run_sync(Order.__table__.create, checkfirst=True)
        logger.info("Ordersテーブルの作成に成功しました（既に存在する場合は作成されません）。")

    except DatabaseError as e:
        raise SQLException(
            sql_statement="CREATE TABLE Orders",
            method_name="create_orders_table()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "create_orders_table()", f"Error: {e}")

'''-----------------------------------------------------------'''
from datetime import date, datetime, timedelta
from typing import List, Optional
from schemas.order_schemas import OrderModel
from database.local_postgresql_database import AsyncSessionLocal

# 選択（１件）
@log_decorator
async def select_single_order(order_id: int) -> Optional[OrderModel]:
    """
    指定されたorder_idに該当するOrdersレコードを、
    Company、MenuテーブルとJOINして必要な情報を取得し、pydanticのOrderModelオブジェクトとして返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.order_id == order_id)
            )
            logger.debug(f"select_single_order() - {stmt=}")
            result = await session.execute(stmt)
            row = result.first()

            if row is None:
                return None

            # Rowオブジェクトは _mapping 属性で辞書のように変換可能です
            row_dict = dict(row._mapping)
            # canceledは整数型の場合があるので、明示的にbool型に変換
            row_dict["canceled"] = bool(row_dict["canceled"])
            order_model = OrderModel(**row_dict)
            return order_model

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise CustomException(500, "select_single_order()", f"SQL実行中にエラーが発生しました: {e}")
    except Exception as e:
        raise CustomException(500, "select_single_order()", f"Error: {e}")


# 選択（全件）
@log_decorator
async def select_all_orders() -> Optional[List[OrderModel]]:
    """
    全てのOrdersレコードを取得し、pydanticのOrderModelのリストとして返します。
    (注文が存在しない場合は None を返します)
    """
    try:
        async with AsyncSessionLocal() as session:
            # CompanyおよびMenuテーブルとJOINして、必要なカラムを取得します
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
            )
            logger.debug(f"select_all_orders() - {stmt=}")

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning("No order found")
                return None

            order_models: List[OrderModel] = []
            for row in rows:
                # SQLAlchemyのRowオブジェクトは _mapping 属性で辞書のようにアクセス可能です
                row_dict = dict(row._mapping)
                # canceledは整数型になっている場合があるため、bool型に変換
                row_dict["canceled"] = bool(row_dict["canceled"])
                # 取得した辞書データをもとに、pydanticモデルOrderModelを生成します
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)

            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_all_orders()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
                print(f"Error: {e}")
        # raise CustomException(500, "select_all_orders()", f"Error: {e}")
'''-----------------------------------------------------------'''
from utils.utils import get_created_at_period

# 選択（一般ユーザー:全件）
@log_decorator
async def select_orders_by_user_all(username: str) -> Optional[List[OrderModel]]:
    """
    指定された username の全 Orders レコードを取得し、
    CompanyおよびMenuテーブルとJOINして必要な情報（company_name, menu_nameなど）を取得、
    その結果をpydanticの OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.username == username)
            )
            logger.debug(f"select_orders_by_user_all() - {stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for user: {username}")
                return None

            order_list: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性で辞書のように変換可能です
                row_dict = dict(row._mapping)
                # canceledカラムは整数型の場合があるため、bool型に変換します
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                order_model = OrderModel(**row_dict)
                order_list.append(order_model)
                
            return order_list

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_user_all()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_user_all()", f"Error: {e}")



# 選択（一般ユーザー:指定日）
@log_decorator
async def select_orders_by_user_at_date(username: str, target_date: date) -> Optional[List[OrderModel]]:
    """
    指定された username と target_date に該当する注文レコードを取得します。
    target_date は datetime.date 型で渡され、Orders.created_at がその日付の
    00:00:00～23:59:59 の範囲の注文を対象とします。
    CompanyおよびMenuテーブルとJOINして、company_name や menu_name など必要な情報を取得し、
    結果を pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            start_dt = f"{target_date.isoformat()} 00:00:00"
            end_dt = f"{target_date.isoformat()} 23:59:59"
            
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(
                    Order.username == username,
                    Order.created_at.between(start_dt, end_dt)
                )
            )
            # SELECT * FROM "Orders"
            # WHERE created_at BETWEEN 
            # '2025-04-22 00:00:00+09'::timestamptz AND 
            # '2025-04-22 23:59:59+09'::timestamptz;

            
            logger.debug(f"select_orders_by_user_at_date() - {stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for user: {username} on {target_date.isoformat()}")
                return None

            order_models: List[OrderModel] = []
            for row in rows:
                row_dict = dict(row._mapping)
                # canceledカラムが整数等の場合、boolに変換
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)
                
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_user_at_date()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_user_at_date()", f"Error: {e}")


# 選択（一般ユーザー:日付遡及）
@log_decorator
async def select_orders_by_user_ago(username: str, days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    指定された username の注文レコードを、本日から指定日数前から本日までの期間に絞り込んで取得します。
    例）days_ago=3 → 本日から３日前～本日の期間の注文を取得する。
    CompanyおよびMenuテーブルとJOINして、必要な情報（company_name, menu_nameなど）を取得し、
    その結果を pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 基本クエリ：username でフィルタし、必要な項目をJOINで取得
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.username == username)
            )

            # # 検証用
            # recent = await session.execute(
            #     select(Order.order_id, Order.created_at)
            #     .where(Order.shop_name == username)
            #     .order_by(Order.created_at.desc())
            #     .limit(5)
            # )
            # for row in recent.fetchall():
            #     print(f"[DEBUG] DB created_at: {row[1]} (type={type(row[1])})")

            # 指定日数前から本日までの期間を取得
            start_dt, end_dt = await get_created_at_period(days_ago)
            print(f"{start_dt=}, {end_dt=}")
            stmt = stmt.where(Order.created_at.between(start_dt, end_dt))
            
            logger.debug(f"select_orders_by_user_ago() - {stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for user: {username} within the specified period")
                return None

            order_models: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性で辞書のように変換可能です
                row_dict = dict(row._mapping)
                # canceled カラムが整数型の場合があるので、明示的に bool() に変換
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)
            
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_user_ago()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_user_ago()", f"Error: {e}")
'''-----------------------------------------------------------'''
from models.company import Company
from models.menu import Menu

@log_decorator
async def select_orders_by_company_all(company_id: int) -> Optional[List[OrderModel]]:
    """
    指定された company_id の注文レコードを、Company および Menu テーブルとJOINして取得します。
    取得結果を pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.company_id == company_id)
            )

            logger.debug(f"- {stmt=}")

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning("No order found for the given company_id")
                return None

            order_models: List[OrderModel] = []
            for row in rows:
                row_dict = dict(row._mapping) # _mapping 属性で変換
                # canceled カラムは整数型の場合があるので bool 型に変換します
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)

            logger.debug(f"- {order_models=}")
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_company_all()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_company_all()", f"Error: {e}")



@log_decorator
async def select_orders_by_company_at_date(company_id: int, target_date: date) -> Optional[List[OrderModel]]:
    """
    指定された company_id と target_date に該当する注文レコードを、
    Company および Menu テーブルとJOINして取得します。
    
    target_date は datetime.date 型で渡され、Orders.created_at がその日付の
    00:00:00～23:59:59 の範囲の注文を対象とします。
    
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    該当する注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # target_date をもとに期間文字列を生成
            start_datetime = f"{target_date.isoformat()} 00:00:00"
            end_datetime   = f"{target_date.isoformat()} 23:59:59"
            
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.company_id == company_id)
                .where(Order.created_at.between(start_datetime, end_datetime))
            )
            
            logger.debug(f"select_orders_by_company_at_date() - {stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning("No order found for the given company_id and target_date")
                return None
            
            order_models: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性で辞書として変換可能です
                row_dict = dict(row._mapping)
                # canceled カラムは整数型の場合があるので、bool型に変換
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)
            
            logger.debug(f"select_orders_by_company_at_date() - order_models: {order_models}")
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_company_at_date()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_company_at_date()", f"Error: {e}")


@log_decorator
async def select_orders_by_company_ago(company_id: int, days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    指定された company_id の注文レコードを、Company および Menu テーブルとJOINして取得します。
    days_ago が指定されている場合、created_at が指定期間内の注文に絞り込みます。
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 基本クエリ: Company, Menu とJOINして必要項目を取得
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.company_id == company_id)
            )


            # 期間指定: days_ago日前から本日までの期間を取得
            start_dt, end_dt = await get_created_at_period(days_ago)
            stmt = stmt.where(Order.created_at.between(start_dt, end_dt))
            logger.debug(f"select_orders_by_company_ago() - {stmt=}")

            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning("No order found for the given company_id")
                return [] 
                #return None
            
            order_models: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性で辞書に変換可能
                row_dict = dict(row._mapping)
                # canceled が数値の場合があるので、明示的に bool に変換
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)
            
            logger.debug(f"select_orders_by_company_ago() - order_models: {order_models}")
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_company_ago()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_company_ago()", f"Error: {e}")

'''-----------------------------------------------------------'''
from datetime import datetime
from typing import Optional, List
import logging

from sqlalchemy import select
from sqlalchemy.exc import DatabaseError

from schemas.order_schemas import OrderModel

logger = logging.getLogger(__name__)

@log_decorator
async def select_orders_by_shop_all(shop_name: str) -> Optional[List[OrderModel]]:
    """
    指定された shop_name に該当する全注文情報を、Company および Menu テーブルとJOINして取得し、
    pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name)
            )
            logger.debug(f"select_orders_by_shop_all() - {stmt=}")
            
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found with the given shop_name: {shop_name}")
                return None
            
            order_models: List[OrderModel] = []
            for row in rows:
                row_dict = dict(row._mapping)

                # DEBUG: created_at の型確認
                logger.debug(f"[DEBUG] created_at type: {type(row_dict.get('created_at'))}, value: {row_dict.get('created_at')}")

                # created_at を文字列から datetime に変換（必要な場合のみ）
                created_at_val = row_dict.get("created_at")
                if isinstance(created_at_val, str):
                    try:
                        row_dict["created_at"] = datetime.fromisoformat(created_at_val)
                    except ValueError:
                        row_dict["created_at"] = datetime.strptime(created_at_val, "%Y-%m-%d %H:%M:%S.%f%z")

                # canceled を bool に明示変換
                row_dict["canceled"] = bool(row_dict.get("canceled", False))

                # OrderModel へ変換
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)
            
            logger.debug(f"select_orders_by_shop_all() - order_models: {order_models}")
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_shop_all()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_shop_all()", f"Error: {e}")




@log_decorator
async def select_orders_by_shop_company(shop_name: str, company_id: int) -> Optional[List[OrderModel]]:
    """
    指定された shop_name と company_id に該当する注文情報を、
    Company および Menu テーブルとJOINして取得します。
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name, Order.company_id == company_id)
            )
            logger.debug(f"select_orders_by_shop_company() - {stmt=}")
            
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for shop: {shop_name} and company_id: {company_id}")
                return None
            
            order_models: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性で辞書に変換可能です
                row_dict = dict(row._mapping)
                # 必要に応じた型変換
                row_dict["order_id"] = int(row_dict["order_id"])
                row_dict["amount"] = int(row_dict["amount"])
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                # 辞書から pydantic モデル OrderModel を生成
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)
            
            logger.debug(f"select_orders_by_shop_company() - order_models: {order_models}")
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_shop_company()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_shop_company()", f"Error: {e}")



@log_decorator
async def select_orders_by_shop_at_date(shop_name: str, target_date: date) -> Optional[List[OrderModel]]:
    """
    指定された shop_name と target_date に該当する注文レコードを取得します。
    
    target_date は datetime.date 型で渡され、Orders.created_at がその日付の
    00:00:00～23:59:59 の範囲内の注文を対象とします。
    
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    該当する注文が存在しなければ None を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # target_dateから期間文字列を生成
            start_datetime = f"{target_date.isoformat()} 00:00:00"
            end_datetime = f"{target_date.isoformat()} 23:59:59"
            
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name)
                .where(Order.created_at.between(start_datetime, end_datetime))
            )
            
            logger.debug(f"select_orders_by_shop_at_date() - {stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning("No order found for the given shop_name and target_date")
                return None

            order_models: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性を利用して辞書に変換できます
                row_dict = dict(row._mapping)
                # order_id, amount を明示的に int型へ変換
                row_dict["order_id"] = int(row_dict["order_id"])
                row_dict["amount"] = int(row_dict["amount"])
                # canceled カラムは整数型等の場合があるため、bool型に変換
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)
            
            logger.debug(f"select_orders_by_shop_at_date() - order_models: {order_models}")
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_shop_at_date()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_shop_at_date()", f"Error: {e}")



@log_decorator
async def select_orders_by_shop_ago(shop_name: str, days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    指定された shop_name の注文レコードを、Company および Menu テーブルとJOINして取得します。
    days_ago が指定されている場合、本日から指定日数前（例：days_ago=3 → 3日前）の開始日から本日までの
    Orders.created_at の範囲内の注文に絞り込みます。
    
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    該当する注文が存在しなければ None を返します。
    """
    print(f"{shop_name=}, {days_ago=}")
    try:
        async with AsyncSessionLocal() as session:
            # JOINして基本クエリを構築
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.canceled
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name)
            )

            # # 検証用
            # print(f"[DEBUG] Querying for orders where created_at BETWEEN {start_dt} AND {end_dt}")
            # recent = await session.execute(
            #     select(Order.order_id, Order.created_at)
            #     .where(Order.shop_name == shop_name)
            #     .order_by(Order.created_at.desc())
            #     .limit(10)
            # )
            # for row in recent.fetchall():
            #     print(f"[DEBUG] DB created_at: {row[1]} (type={type(row[1])})")

            # 指定日数前から本日までの期間を取得
            start_dt, end_dt = await get_created_at_period(days_ago)
            # print(f"start_dt: {start_dt}, end_dt: {end_dt}")

            # 期間条件を追加
            print(f"days_ago: {days_ago}")
            if days_ago == 0:
                stmt = stmt.where(
                    Order.created_at >= start_dt,
                    Order.created_at <= start_dt + timedelta(days=1)
                )
            else:
                stmt = stmt.where(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt  # ここは `<=` にするのが素直で安全
                )
            # stmt = stmt.where(Order.created_at.between(start_dt, end_dt))
            # print(f"{start_dt=}, {end_dt=}")
            # logger.info(f"{stmt=}")
            print(f"str(stmt):--->{str(stmt)}")

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning("No order found for the given shop_name with the specified period")
                return []# return None

            print(f"rows count: {len(rows)}")

            order_models: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性で辞書に変換可能
                row_dict = dict(row._mapping)
                # 必要に応じた型変換
                row_dict["order_id"] = int(row_dict["order_id"])
                row_dict["amount"] = int(row_dict["amount"])
                row_dict["canceled"] = bool(row_dict.get("canceled", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)

            logger.debug(f"{order_models=}")
            return order_models

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_shop_ago()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "select_orders_by_shop_ago()", f"Error: {e}")


'''-------------------------------------------------------------'''
# 追加
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError
from sqlalchemy import text
import traceback

from log_unified import order_logger

@log_decorator
async def insert_order(
    company_id: int,
    username: str,
    shop_name: str,
    menu_id: int,
    amount: int,
    created_at: Optional[datetime] = None
) -> int:
    """
    Ordersテーブルに新規注文を挿入する関数です。
    created_atがNoneの場合は、Asia/Tokyoの現在時刻（ナイーブなdatetime）を設定します。
    """

    try:
        async with AsyncSessionLocal() as session:
            if created_at is None:
                created_at = get_today_datetime()

            # 念のため tzinfo を削除（ナイーブ化）
            if created_at.tzinfo is not None:
                created_at = created_at.replace(tzinfo=None)

            logger.debug(f"insert_order() - 使用する created_at: {created_at} (tzinfo={created_at.tzinfo})")

            new_order = Order(
                company_id=company_id,
                username=username,
                shop_name=shop_name,
                menu_id=menu_id,
                amount=amount,
                created_at=created_at,
                canceled=0
            )
            session.add(new_order)
            await session.commit()
            await session.refresh(new_order)

            order_id = new_order.order_id

            # やはりここがおかしい
            # logger.debug(f"insert_order() - 新規注文の値: {company_id=}, {username=}, {shop_name=}, {menu_id=}, {amount=}, {created_at=}")
            order_logger.info("ORDER", f"注文完了 - order_id:{order_id} - {company_id}:{username}, {shop_name}:{menu_id}, {amount}")
            # order_logger.info("ORDER - 注文が完了しました")

            return order_id

    except IntegrityError as e:
        session.rollback()
        print("データベースの制約違反:", e)
    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement="OrdersテーブルへのINSERT中に発生",
            method_name="insert_order()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")


'''-------------------------------------------------------------'''
# 更新
from sqlalchemy import update

@log_decorator
async def update_order(order_id: int, canceled: bool):
    """
    指定された order_id の注文レコードに対して、canceled フラグと updated_at を更新します。
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SET TIME ZONE 'Asia/Tokyo'"))  # タイムゾーン設定

            current_time = get_today_datetime()
            stmt = (
                update(Order)
                .where(Order.order_id == order_id)
                .values(canceled=canceled, updated_at=current_time)
            )
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                logger.warning(f"注文更新失敗: order_id {order_id} の注文が見つかりませんでした。")
            else:
                logger.info(f"注文更新成功: order_id {order_id}")
            logger.debug(f"update_order() - SQL: {stmt}")

    except IntegrityError as e:
        session.rollback()
        print("データベースの制約違反:", e)
    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="update_order()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "update_order()", f"Error: {e}")
'''-------------------------------------------------------------'''
# 削除（指定ID）
from sqlalchemy import delete, text

@log_decorator
async def delete_order(order_id: int) -> bool:
    """
    指定された order_id の Order レコードを削除します。
    削除対象が存在しなければ False を返し、削除に成功すれば True を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(Order).where(Order.order_id == order_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                logger.warning(f"Order with order_id {order_id} not found.")
                return False

            logger.info(f"Order with order_id {order_id} deleted successfully.")
            return True

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="delete_order()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "delete_order()", f"Error: {e}")


# 削除（全件）
@log_decorator
async def delete_all_orders():
    sqlstr = "DROP TABLE IF EXISTS orders"
    try:
        def drop_table(sync_conn):
            sync_conn.execute(text(sqlstr))

        async with AsyncSessionLocal() as session:
            await session.run_sync(drop_table)

    except OperationalError as e:
        session.rollback()
        print("データベース接続の問題:", e)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=sqlstr,
            method_name="delete_all_orders()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        print(f"Error: {e}")
        # raise CustomException(500, "delete_all_orders()", f"Error: {e}")
