# models/order.py
'''
    注文クエリ関数

    1. class Order(Base):
    2. create_orders_table():

    # 一般ユーザー(username) を指定して、注文を取得する
    3. select_orders_by_user_all(username: str) -> Optional[List[OrderModel]]:
    4. select_orders_by_user_at_date(username: str, target_date: date) -> Optional[List[OrderModel]]:
    5. select_orders_by_user_at_date_range(username: str, start: datetime, end: datetime) -> Optional
    6. select_orders_by_user_ago(username: str, days_ago: int = 0) -> Optional[List[OrderModel]]:

    # 契約企業(company_id) を指定して、注文を取得する
    7. select_orders_by_company_all(company_id: int) -> Optional[List[OrderModel]]:
    8. select_orders_by_company_at_date(company_id: int, target_date: date) -> Optional[List[OrderModel]]:
    9. select_orders_by_company_at_date_range(company_id: int, start_date: date, end_date: date) -> Optional[List[OrderModel]]:
    10. select_orders_by_company_ago(company_id: int, days_ago_str: str = None) -> Optional[List[OrderModel]]:

    # 店舗(shop_name) を指定して、注文を取得する
    11. select_orders_by_shop_all(shop_name: str) -> Optional[List[OrderModel]]:
    12. select_orders_by_shop_company(shop_name: str, company_id: int) -> Optional[List[OrderModel]]:
    13. select_orders_by_shop_at_date(shop_name: str, target_date: date) -> Optional[List[OrderModel]]:
    14. select_orders_by_shop_at_date_range(shop_name: str, start_date: date, end_date: date) -> Optional[List[OrderModel]]:
    15. select_orders_by_shop_ago(shop_name: str, days_ago_str: str) -> Optional[List[OrderModel]]:

    # 管理者(admin)用に注文を取得する
    16. select_single_order(order_id: int) -> OrderModel:
    17. select_all_orders() -> Optional[List[OrderModel]]:
    18. select_orders_by_admin_at_date(target_date: date) -> Optional[List[OrderModel]]:
    19. select_orders_by_admin_at_date_range(start_date: date, end_date: date) -> Optional[List[OrderModel]]:
    20. select_orders_by_admin_ago(days_ago: int = 0) -> Optional[List[OrderModel]]:

    21. insert_order(company_id: int, username: str, shop_name: str, menu_id: int, amount: int, created_at: Optional[str] = None) -> int:
    22. update_order(order_id: int, company_id: int, username: str, shop_name: str, menu_id: int, amount: int, updated_at: Optional[str] = None) -> bool:
    23. delete_order(order_id: int) -> bool:
    24. delete_all_orders():
    
    25. get_datetime_range_for_date(target_date) -> start_dt, end_dt
    26. select_order_summary(conditions: Dict) -> Dict:
'''
from sqlalchemy import Column, Integer, String, DateTime, Date, func
from database.local_postgresql_database import Base, engine

# SELECT * FROM public."Orders"
# ORDER BY order_id DESC

# モデルクラス定義
class Order(Base):
    __tablename__ = "Orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer)
    username = Column(String)
    shop_name = Column(String)
    menu_id = Column(Integer)
    amount = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())  # 作成日時(サーバー側作成日時)
    updated_at = Column(DateTime, nullable=True)
    expected_delivery_date = Column(Date, nullable=True)
    checked = Column(Integer, default=0)

    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


import logging
logger = logging.getLogger(__name__)
from log_unified import logger

from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError

from utils.utils import log_decorator

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

    except DatabaseError as e:
        engine.rollback()
        logger.error(f"SQL実行中にエラーが発生しました: {e}")
    except Exception as e:
        engine.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        logger.info("Ordersテーブルの作成に成功しました（既に存在する場合は作成されません）。")


'''-----------------------------------------------------------'''
from datetime import date, datetime, timedelta
from typing import List, Optional
from schemas.order_schemas import OrderModel
from database.local_postgresql_database import AsyncSessionLocal

# 選択（一般ユーザー:全件）
@log_decorator
async def select_orders_by_user_all(username: str) -> Optional[List[OrderModel]]:
    """
    指定された username の全 Orders レコードを取得し、
    CompanyおよびMenuテーブルとJOINして必要な情報（company_name, menu_nameなど）を取得、
    その結果をpydanticの OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ [] を返します。
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.username == username)
            )
            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for user: {username}")
                return []# return None

            # order_list: List[OrderModel] = []
            # for row in rows:
            #     # Rowオブジェクトは _mapping 属性で辞書のように変換可能です
            #     row_dict = dict(row._mapping)
            #     # checkedカラムは整数型の場合があるため、bool型に変換します
            #     row_dict["checked"] = bool(row_dict.get("checked", False))
            #     order_model = OrderModel(**row_dict)
            #     order_list.append(order_model)
            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

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
        return order_models#order_list


# 選択（一般ユーザー: 日付指定）
@log_decorator
async def select_orders_by_user_at_date(username: str, target_date: date) -> Optional[List[OrderModel]]:
    """
    指定された username と target_date に該当する注文レコードを取得します。
    target_date は datetime.date 型で渡され、Orders.created_at がその日付の
    00:00:00～23:59:59 の範囲の注文を対象とします。
    CompanyおよびMenuテーブルとJOINして、company_name や menu_name など必要な情報を取得し、
    結果を pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ [] を返します。
    """
    # from datetime import time
    try:
        async with AsyncSessionLocal() as session:
            start_dt, end_dt = get_datetime_range_for_date(target_date)
            
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(
                    Order.username == username,
                    Order.created_at.between(start_dt, end_dt)
                )
            )

            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for user: {username} on {target_date.isoformat()}")
                return []# return None

            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

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
        return order_models

# 選択（一般ユーザー:開始日から終了日まで）
@log_decorator
async def select_orders_by_user_at_date_range(username: str, start: datetime, end: datetime) -> Optional[List[OrderModel]]:
    """
    指定された username と start ~ end 期間に該当する注文レコードを取得します。
    CompanyおよびMenuテーブルとJOINして、company_name や menu_name など必要な情報を取得し、
    結果を pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ [] を返します。
    """
    try:
        start_datetime = datetime.combine(start, time.min)
        end_datetime = datetime.combine(end, time.max)
        
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(
                    Order.username == username,
                    Order.created_at.between(start_datetime, end_datetime)
                )
            )

            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning(f"No order found for user: {username} between {start} and {end}")
                return []

            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました: {e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        return order_models

from utils.utils import get_datetime_range
from datetime import time

# 選択（一般ユーザー:日付遡及）
@log_decorator
async def select_orders_by_user_ago(username: str, days_ago: int = 0) -> Optional[List[OrderModel]]:

    # 遡及日を求める
    now = datetime.now()
    start = now - timedelta(days=days_ago)
    end = now
    
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end, time.max)
    
    return await select_orders_by_user_at_date_range(username, start_dt, end_dt)

@log_decorator
async def select_orders_by_user_ago_old(username: str, days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    指定された username の注文レコードを、本日から指定日数前から本日までの期間に絞り込んで取得します。
    例）days_ago=3 → 本日から３日前～本日の期間の注文を取得する。
    CompanyおよびMenuテーブルとJOINして、必要な情報（company_name, menu_nameなど）を取得し、
    その結果を pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ [] を返します。
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.username == username)
            )

            start_dt, end_dt = await get_datetime_range(days_ago)
            stmt = stmt.where(Order.created_at.between(start_dt, end_dt))

            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning(f"No order found for user: {username} within the specified period days_ago: {days_ago}")
                return []# return None

            order_models: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性で辞書のように変換可能です
                row_dict = dict(row._mapping)
                # checked カラムが整数型の場合があるので、明示的に bool() に変換
                row_dict["checked"] = bool(row_dict.get("checked", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)

            return order_models

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


'''-----------------------------------------------------------'''
from models.company import Company
from models.menu import Menu

# 選択（契約企業ユーザー:全件）
@log_decorator
async def select_orders_by_company_all(company_id: int) -> Optional[List[OrderModel]]:
    """
    指定された company_id の注文レコードを、Company および Menu テーブルとJOINして取得します。
    取得結果を pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ [] を返します。
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.company_id == company_id)
            )

            logger.debug(f"{stmt=}")

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning(f"No order found for the given company_id: {company_id}")
                return []# return None

            # order_models: List[OrderModel] = []
            # for row in rows:
            #     row_dict = dict(row._mapping) # _mapping 属性で変換
            #     # checked カラムは整数型の場合があるので bool 型に変換します
            #     row_dict["checked"] = bool(row_dict.get("checked", False))
            #     order_model = OrderModel(**row_dict)
            #     order_models.append(order_model)
            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

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
        logger.debug(f"- {order_models=}")
        return order_models

# 選択（契約企業ユーザー: 日付指定）
@log_decorator
async def select_orders_by_company_at_date(company_id: int, target_date: date) -> Optional[List[OrderModel]]:
    """
    指定された company_id と target_date に該当する注文レコードを、
    Company および Menu テーブルとJOINして取得します。
    
    target_date は datetime.date 型で渡され、Orders.created_at がその日付の
    00:00:00～23:59:59 の範囲の注文を対象とします。
    
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    該当する注文が存在しなければ [] を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # target_date をもとに期間文字列を生成
            start_dt, end_dt = get_datetime_range_for_date(target_date)

            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.company_id == company_id)
                .where(Order.created_at.between(start_dt, end_dt))
            )
            
            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for the given company_id:{company_id} and target_date: {target_date}")
                return []# return None
            
            # order_models: List[OrderModel] = []
            # for row in rows:
            #     # Rowオブジェクトは _mapping 属性で辞書として変換可能です
            #     row_dict = dict(row._mapping)
            #     # checked カラムは整数型の場合があるので、bool型に変換
            #     row_dict["checked"] = bool(row_dict.get("checked", False))
            #     order_model = OrderModel(**row_dict)
            #     order_models.append(order_model)
            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

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
        logger.debug(f"{order_models=}")
        return order_models


# 選択（契約企業ユーザー:開始日から終了日まで）
@log_decorator
async def select_orders_by_company_at_date_range(company_id: int, start_date: date, end_date: date) -> Optional[List[OrderModel]]:
    """
    指定された company_id と日付範囲（start_date ~ end_date）の注文レコードを取得します。
    """
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)

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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.company_id == company_id)
                .where(Order.created_at.between(start_datetime, end_datetime))
            )
            
            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for company_id: {company_id} between {start_date} and {end_date}")
                return []

            # order_models: List[OrderModel] = []
            # for row in rows:
            #     row_dict = dict(row._mapping)
            #     row_dict["checked"] = bool(row_dict.get("checked", False))
            #     order_models.append(OrderModel(**row_dict))
            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"DatabaseError: {e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        return order_models


# 選択（契約企業ユーザー:日付遡及）
@log_decorator
async def select_orders_by_company_ago(company_id: int, days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    指定された company_id の注文レコードを、days_ago日前から本日までの期間で取得します。
    """
    now = datetime.now().date()
    start_date = now - timedelta(days=days_ago)
    end_date = now

    return await select_orders_by_company_at_date_range(company_id, start_date, end_date)

@log_decorator
async def select_orders_by_company_ago_old(company_id: int, days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    指定された company_id の注文レコードを、Company および Menu テーブルとJOINして取得します。
    days_ago が指定されている場合、created_at が指定期間内の注文に絞り込みます。
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    注文が存在しなければ [] を返します。
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.company_id == company_id)
            )


            # 期間指定: days_ago日前から本日までの期間を取得
            start_dt, end_dt = await get_datetime_range(days_ago)
            stmt = stmt.where(Order.created_at.between(start_dt, end_dt))
            logger.debug(f"{stmt=}")

            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for the given company_id: {company_id}")
                return []# return None

            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

            logger.debug(f"select_orders_by_company_ago() - order_models: {order_models}")

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
        return order_models


'''-----------------------------------------------------------'''
from typing import Optional, List

from sqlalchemy import select

from schemas.order_schemas import OrderModel

logger = logging.getLogger(__name__)

# 選択（店舗ユーザー:全件）
@log_decorator
async def select_orders_by_shop_all(shop_name: str) -> Optional[List[OrderModel]]:
    """
    指定された shop_name に該当する全注文情報を、Company および Menu テーブルとJOINして取得し、
    pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ [] を返します。
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name)
            )
            
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found with the given shop_name: {shop_name}")
                return []# return None
            
            order_models: List[OrderModel] = []
            for row in rows:
                row_dict = dict(row._mapping)

                # DEBUG: created_at の型確認
                # logger.debug(f"[DEBUG] created_at type: {type(row_dict.get('created_at'))}, value: {row_dict.get('created_at')}")

                # created_at を文字列から datetime に変換（必要な場合のみ）
                created_at_val = row_dict.get("created_at")
                if isinstance(created_at_val, str):
                    try:
                        row_dict["created_at"] = datetime.fromisoformat(created_at_val)
                    except ValueError:
                        row_dict["created_at"] = datetime.strptime(created_at_val, "%Y-%m-%d %H:%M:%S.%f%z")

                # checked を bool に明示変換
                row_dict["checked"] = bool(row_dict.get("checked", False))

                # OrderModel へ変換
                # order_model = OrderModel(**row_dict)
                # order_models.append(order_model)
                order_models = []
                for row in rows:
                    row_dict = dict(row._mapping)
                    row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                    order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
        logger.debug(f"{stmt=}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
        logger.debug(f"{stmt=}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
        logger.debug(f"{stmt=}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
        logger.debug(f"{stmt=}")
    else:
        logger.debug(f"select_orders_by_shop_all() - order_models: {order_models}")
        return order_models


# 選択（店舗ユーザー:店舗・契約企業指定）
@log_decorator
async def select_orders_by_shop_company(shop_name: str, company_id: int) -> Optional[List[OrderModel]]:
    """
    指定された shop_name と company_id に該当する注文情報を、
    Company および Menu テーブルとJOINして取得します。
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    注文が存在しなければ [] を返します。
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name, Order.company_id == company_id)
            )
            
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for shop: {shop_name} and company_id: {company_id}")
                return []# return None

            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない
            # order_models: List[OrderModel] = []
            # for row in rows:
            #     # Rowオブジェクトは _mapping 属性で辞書に変換可能です
            #     row_dict = dict(row._mapping)
            #     # 必要に応じた型変換
            #     row_dict["order_id"] = int(row_dict["order_id"])
            #     row_dict["amount"] = int(row_dict["amount"])
            #     row_dict["checked"] = bool(row_dict.get("checked", False))
            #     # 辞書から pydantic モデル OrderModel を生成
            #     order_model = OrderModel(**row_dict)
            #     order_models.append(order_model)

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
        logger.debug(f"{stmt=}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
        logger.debug(f"{stmt=}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
        logger.debug(f"{stmt=}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
        logger.debug(f"{stmt=}")
    else:
        logger.debug(f"select_orders_by_shop_company() - order_models: {order_models}")
        return order_models


# 選択（店舗ユーザー:日付指定）
@log_decorator
async def select_orders_by_shop_at_date(shop_name: str, target_date: date) -> Optional[List[OrderModel]]:
    """
    指定された shop_name と target_date に該当する注文レコードを取得します。
    
    target_date は datetime.date 型で渡され、Orders.created_at がその日付の
    00:00:00～23:59:59 の範囲内の注文を対象とします。
    
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    該当する注文が存在しなければ [] を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # target_dateから期間文字列を生成
            start_dt, end_dt = get_datetime_range_for_date(target_date)
            print(f"{start_dt=},{end_dt=}")
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name)
                .where(Order.created_at.between(start_dt, end_dt))
            )

            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for the given shop_name: {shop_name} and target_date: {target_date}")
                return []# return None

            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
        logger.debug(f"{stmt=}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
        logger.debug(f"{stmt=}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
        logger.debug(f"{stmt=}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
        logger.debug(f"{stmt=}")
    else:
        logger.debug(f"select_orders_by_shop_at_date() - order_models: {order_models}")
        return order_models


# 選択（店舗ユーザー:開始日から終了日まで）
@log_decorator
async def select_orders_by_shop_at_date_range(shop_name: str, start_date: date, end_date: date) -> Optional[List[OrderModel]]:
    """
    指定された shop_name と日付範囲（start_date ~ end_date）の注文レコードを取得します。
    """
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name)
                .where(Order.created_at.between(start_datetime, end_datetime))
            )
            
            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No orders found for shop: {shop_name} between {start_date} and {end_date}")
                return []

            # order_models: List[OrderModel] = []
            # for row in rows:
            #     row_dict = dict(row._mapping)
            #     row_dict["checked"] = bool(row_dict.get("checked", False))
            #     order_models.append(OrderModel(**row_dict))
            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"DatabaseError: {e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        return order_models


# 選択（店舗ユーザー:日付遡及）
@log_decorator
async def select_orders_by_shop_ago(shop_name: str, days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    指定された shop_name の注文レコードを、days_ago日前から本日までの期間で取得します。
    """
    now = datetime.now().date()
    start_date = now - timedelta(days=days_ago)
    end_date = now

    return await select_orders_by_shop_at_date_range(shop_name, start_date, end_date)


@log_decorator
async def select_orders_by_shop_ago_old(shop_name: str, days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    指定された shop_name の注文レコードを、Company および Menu テーブルとJOINして取得します。
    days_ago が指定されている場合、本日から指定日数前（例：days_ago=3 → 3日前）の開始日から本日までの
    Orders.created_at の範囲内の注文に絞り込みます。
    
    取得結果は pydantic の OrderModel オブジェクトのリストとして返し、
    該当する注文が存在しなければ [] を返します。
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.shop_name == shop_name)
            )

            # 指定日数前から本日までの期間を取得
            start_dt, end_dt = await get_datetime_range(days_ago)

            # 期間条件を追加
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

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning(f"No order found for the given shop_name: {shop_name} with the specified start_dt: {start_dt}, end_dt: {end_dt}")
                return []# return None

            print(f"rows count: {len(rows)}")

            order_models: List[OrderModel] = []
            for row in rows:
                # Rowオブジェクトは _mapping 属性で辞書に変換可能
                row_dict = dict(row._mapping)
                # 必要に応じた型変換
                row_dict["order_id"] = int(row_dict["order_id"])
                row_dict["amount"] = int(row_dict["amount"])
                row_dict["checked"] = bool(row_dict.get("checked", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)

            logger.debug(f"{order_models=}")

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
        logger.error(f"{stmt=}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
        logger.error(f"{stmt=}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
        logger.error(f"{stmt=}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
        logger.error(f"{stmt=}")
    else:
        return order_models


'''-----------------------------------------------------------'''
# 管理者ユーザーの場合
# 選択（管理者ユーザー:１件）
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.order_id == order_id)
            )
            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            row = result.first()

            if row is None:
                logger.warning("No order found")
                return []

            # Rowオブジェクトは _mapping 属性で辞書のように変換可能です
            row_dict = dict(row._mapping)
            # checkedは整数型の場合があるので、明示的にbool型に変換
            row_dict["checked"] = bool(row_dict["checked"])
            order_model = OrderModel(**row_dict)

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
        return order_model

# 選択（管理者ユーザー:全件）
@log_decorator
async def select_all_orders() -> Optional[List[OrderModel]]:
    """
    全てのOrdersレコードを取得し、pydanticのOrderModelのリストとして返します。
    (注文が存在しない場合は [] を返します)
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
            )
            logger.debug(f"{stmt=}")

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning("No order found")
                return []# return None


            # order_models: List[OrderModel] = []
            # for row in rows:
            #     # SQLAlchemyのRowオブジェクトは _mapping 属性で辞書のようにアクセス可能です
            #     row_dict = dict(row._mapping)
            #     # checkedは整数型になっている場合があるため、bool型に変換
            #     row_dict["checked"] = bool(row_dict["checked"])
            #     # 取得した辞書データをもとに、pydanticモデルOrderModelを生成します
            #     order_model = OrderModel(**row_dict)
            #     order_models.append(order_model)
            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

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
        return order_models


# 選択（管理者ユーザー:日付指定）
@log_decorator
async def select_orders_by_admin_at_date(target_date: date) -> Optional[List[OrderModel]]:
    """
    管理者用。指定日の全注文を取得。
    """
    start_dt, end_dt = get_datetime_range_for_date(target_date)

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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.created_at.between(start_dt, end_dt))
            )
            
            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No orders found on {target_date}")
                return []

            # order_models = [OrderModel(**dict(row._mapping), checked=bool(dict(row._mapping).get("checked", False))) for row in rows]
            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        return order_models


# 選択（管理者ユーザー:開始日から終了日まで）
@log_decorator
async def select_orders_by_admin_at_date_range(start_date: date, end_date: date) -> Optional[List[OrderModel]]:
    """
    管理者用。指定日付範囲内の全注文を取得。
    """
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)
    
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
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
                .where(Order.created_at.between(start_datetime, end_datetime))
            )
            
            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No orders found between {start_date} and {end_date}")
                return []

            # order_models = [OrderModel(**dict(row._mapping), checked=bool(dict(row._mapping).get("checked", False))) for row in rows]
            order_models = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))  # ここで変換
                order_models.append(OrderModel(**row_dict))  # ここでは重複指定しない

    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
    else:
        return order_models


# 選択（管理者ユーザー:日付遡及）
@log_decorator
async def select_orders_ago(days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    管理者用。days_ago日前から本日までの全注文を取得。
    """
    now = datetime.now().date()
    start_date = now - timedelta(days=days_ago)
    end_date = now

    return await select_orders_at_date_range(start_date, end_date)


@log_decorator
async def select_orders_by_admin_ago_old(days_ago: int = 0) -> Optional[List[OrderModel]]:
    """
    管理者用。usernameフィルタを行わず、指定日数前から本日までの全注文レコードを取得します。
    CompanyおよびMenuテーブルとJOINして、必要な情報を取得し、
    pydantic の OrderModel オブジェクトのリストとして返します。
    注文が存在しなければ [] を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # username フィルタ無し
            stmt = (
                select(
                    Order.order_id,
                    Company.name.label("company_name"),
                    Order.username,
                    Order.shop_name,
                    Menu.name.label("menu_name"),
                    Order.amount,
                    Order.created_at,
                    Order.expected_delivery_date,
                    Order.checked
                )
                .select_from(Order)
                .join(Company, Order.company_id == Company.company_id)
                .join(Menu, Order.menu_id == Menu.menu_id)
            )

            # 日付範囲フィルタのみ適用
            start_dt, end_dt = await get_datetime_range(days_ago)
            stmt = stmt.where(Order.created_at.between(start_dt, end_dt))

            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning(f"No orders found within the specified period days_ago: {days_ago}")
                return []

            order_models: List[OrderModel] = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["checked"] = bool(row_dict.get("checked", False))
                order_model = OrderModel(**row_dict)
                order_models.append(order_model)

            return order_models

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

'''-------------------------------------------------------------'''
# 追加
from log_unified import log_order
from utils.utils import get_naive_jst_now
from config.config_loader import skip_holiday

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
                created_at = get_naive_jst_now()
                print(f"1: {created_at=}")

            # 念のため tzinfo を削除（ナイーブ化）
            if created_at.tzinfo is not None:
                created_at = created_at.replace(tzinfo=None)
                print(f"2: {created_at=}")

            logger.debug(f"insert_order() - 使用する created_at: {created_at} (tzinfo={created_at.tzinfo})")
            # 配達予定日を取得し、printで確認
            delivery_date = await skip_holiday(created_at)

            new_order = Order(
                company_id=company_id,
                username=username,
                shop_name=shop_name,
                menu_id=menu_id,
                amount=amount,
                created_at=created_at,
                expected_delivery_date=delivery_date,  # 追加
                checked=0
            )
            session.add(new_order)
            await session.commit()
            await session.refresh(new_order)

            order_id = new_order.order_id

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
        logger.info(f"注文が完了しました - order_id:{order_id} ")
        log_order(
            "ORDER",
            f"注文完了 - order_id:{order_id:>4} - company_id:{company_id}, username:{username}, shop_name:{shop_name}, menu_id:{menu_id}, amount:{amount}"
        )
        return order_id

'''-------------------------------------------------------------'''
# 更新
from sqlalchemy import update, text
from utils.utils import get_naive_jst_now

@log_decorator
async def update_order(order_id: int, checked: bool):
    """
    指定された order_id の注文レコードに対して、checked フラグと updated_at を更新します。
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SET TIME ZONE 'Asia/Tokyo'"))  # タイムゾーン設定

            updated_time = get_naive_jst_now()
            stmt = (
                update(Order)
                .where(Order.order_id == order_id)
                .values(checked=checked, updated_at=updated_time)
            )
            result = await session.execute(stmt)
            await session.commit()

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
        logger.error(f"{stmt=}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
        logger.error(f"{stmt=}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
        logger.error(f"{stmt=}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
        logger.error(f"{stmt=}")
    else:
        if result.rowcount == 0:
            logger.warning(f"注文更新失敗: order_id {order_id} の注文が見つかりませんでした。")
            logger.error(f"{stmt=}")
        else:
            logger.info(f"注文更新成功: order_id {order_id}")
        logger.debug(f"update_order() - SQL: {stmt}")

'''-------------------------------------------------------------'''
# 削除（指定ID）
from sqlalchemy import delete

@log_decorator
async def delete_order(order_id: int) -> bool:
    """
    指定された order_id の Order レコードを削除します。
    削除対象が存在しなければ False を返し、削除に成功すれば True を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(Order).where(Order.order_id == order_id)
            logger.debug(f"{stmt=}")
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                logger.warning(f"Order with order_id {order_id} not found.")
                return False

            # return True

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
        logger.error(f"{stmt=}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
        logger.error(f"{stmt=}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
        logger.error(f"{stmt=}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
        logger.error(f"{stmt=}")
    else:
        logger.info(f"Order with order_id {order_id} deleted successfully.")
        return True


# 削除（全件）
@log_decorator
async def delete_all_orders():
    stmt = "DROP TABLE IF EXISTS orders"
    try:
        def drop_table(sync_conn):
            sync_conn.execute(text(stmt))

        async with AsyncSessionLocal() as session:
            await session.run_sync(drop_table)

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError: {e}")
        logger.error(f"{stmt=}")
    except OperationalError as e:
        await session.rollback()
        logger.error(f"OperationalError: {e}")
        logger.error(f"{stmt=}")
    except DatabaseError as e:
        await session.rollback()
        logger.error(f"SQL実行中にエラーが発生しました:{e}")
        logger.error(f"{stmt=}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
        logger.error(f"{stmt=}")
    else:
        logger.info("All orders deleted successfully.")
        log_order(
            "ORDER",
            f"全ての注文を削除しました。"
        )

'''-------------------------------------------------------------'''
from datetime import date, datetime, time
from typing import Tuple


def get_datetime_range_for_date(target_date: date) -> Tuple[datetime, datetime]:
    """
    指定された日付 (date) から 00:00:00 ～ 23:59:59.999999 の datetime 範囲を返す。
    例: 2025-05-19 → (2025-05-19 00:00:00, 2025-05-19 23:59:59.999999)
    """
    start_datetime = datetime.combine(target_date, time.min)
    end_datetime = datetime.combine(target_date, time.max)
    return start_datetime, end_datetime


# 概要出力：本日の注文件数を返す
from typing import Dict
@log_decorator
async def select_order_summary(conditions: Dict) -> Dict:
    """
    今日の注文合計数を返す。
    条件に基づいて user_id, company_id, shop_id, is_admin で絞り込み。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 基本クエリ：注文件数をカウント
            stmt = select(func.count()).select_from(Order)

            # 日付範囲絞り込み
            begin_date = conditions.get("begin_date")
            end_date = conditions.get("end_date")
            if begin_date and end_date:
                stmt = stmt.where(Order.created_at.between(f"{begin_date} 00:00:00", f"{end_date} 23:59:59"))

            # 各種条件追加
            if conditions.get("user_id"):
                stmt = stmt.where(Order.username == conditions["user_id"])
            if conditions.get("company_id"):
                stmt = stmt.where(Order.company_id == conditions["company_id"])
            if conditions.get("shop_id"):
                stmt = stmt.where(Order.shop_name == conditions["shop_id"])
            # is_admin は全件なので条件追加なし

            logger.debug(f"Order Summary SQL: {stmt}")

            result = await session.execute(stmt)
            total_orders = result.scalar() or 0

            return {"total_orders": total_orders}

    except Exception as e:
        logger.exception(f"select_order_summary error: {e}")
        return {"total_orders": 0}

'''-------------------------------------------------------------'''
