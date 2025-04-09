# database/orders.py
'''
    注文クエリ

    1. class Orders(Base):
    2. create_orders_table():

    # 管理者用に1件・全件取得する
    3. select_single_order(order_id: int) -> Orders:
    4. select_all_orders() -> Optional[List[Orders]]:

    # 一般ユーザー(username) を指定して、注文を取得する
    5. select_orders_by_user_all(username: str) -> Optional[List[Orders]]:
    6. select_orders_by_user_at_date(username: str, target_date: date) -> Optional[List[Orders]]:
    7. select_orders_by_user_ago(username: str, days_ago: int = 0) -> Optional[List[Orders]]:

    # 会社発注者(company_id) を指定して、注文を取得する
    8. select_orders_by_company_all(company_id: int) -> Optional[List[Orders]]:
    9. select_orders_by_company_at_date(company_id: int, target_date: date) -> Optional[List[Orders]]:
    10. select_orders_by_company_ago(company_id: int, days_ago_str: str = None) -> Optional[List[Orders]]:

    # 店舗名(shop_name) を指定して、注文を取得する
    11. select_orders_by_shop_all(shop_name: str) -> Optional[List[Orders]]:
    12. select_orders_by_shop_company(shop_name: str, company_id: int) -> Optional[List[Orders]]:
    13. select_orders_by_shop_at_date(shop_name: str, target_date: date) -> Optional[List[Orders]]:
    14. select_orders_by_shop_ago(shop_name: str, days_ago_str: str) -> Optional[List[Orders]]:
    
    15. insert_order(company_id: int, username: str, shop_name: str, menu_id: int, amount: int, created_at: Optional[str] = None) -> int:
    16. update_order(order_id: int, company_id: int, username: str, shop_name: str, menu_id: int, amount: int, updated_at: Optional[str] = None) -> bool:
    17. delete_order(order_id: int) -> bool:
    18. delete_all_orders():
'''
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.exc import DatabaseError
#from sqlalchemy_database import Base, AsyncSessionLocal
from .sqlalchemy_database import Base, AsyncSessionLocal

from order_log_config import order_logger


class Orders(Base):
    __tablename__ = "Orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer)
    username = Column(String)
    shop_name = Column(String)
    menu_id = Column(Integer)
    amount = Column(Integer)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, default="")
    canceled = Column(Integer, default=0)

    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


from utils.exception import CustomException, SQLException
from utils.utils import log_decorator



import logging
logger = logging.getLogger(__name__)

# 作成
@log_decorator
async def create_orders_table():
    """
    Ordersテーブルを作成する（存在しなければ作成）
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.run_sync(Orders.__table__.create, checkfirst=True)
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

from datetime import date
from typing import List, Optional

'''-------------------------------------------------------------'''
# 選択（１件）
@log_decorator
async def select_single_order(order_id: int) -> Orders:
    """
    指定されたorder_idに該当するOrdersレコードを取得する
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Orders).where(Orders.order_id == order_id)
            result = await session.execute(stmt)
            order = result.scalars().first()
            logger.debug(f"select_single_order() - SQLAlchemyクエリ: {stmt}")
            return order
    except DatabaseError as e:
        raise CustomException(500, "select_single_order()", f"SQL実行中にエラーが発生しました: {e}")
    except Exception as e:
        raise CustomException(500, "select_single_order()", f"Error: {e}")


# 選択（全件）
@log_decorator
async def select_all_orders() -> Optional[List[Orders]]:
    """
    全てのOrdersレコードを取得し、Ordersオブジェクトのリストとして返す
    (注文が存在しない場合は None を返します)
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Orders)
            result = await session.execute(stmt)
            orders_list = result.scalars().all()

            if not orders_list:
                logger.warning("No order found")
                return None

            logger.debug(f"select_all_orders() - SQLAlchemyクエリ: {stmt}")
            return orders_list

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_all_orders()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_all_orders()", f"Error: {e}")

'''-------------------------------------------------------------'''
from utils.utils import get_created_at_period

# 選択（一般ユーザー:全件）
@log_decorator
async def select_orders_by_user_all(username: str) -> Optional[List[Orders]]:
    """
    指定された username の全 Orders レコードを取得する。
    戻り値は Orders オブジェクトのリスト（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Orders).where(Orders.username == username)
            logger.debug(f"select_orders_by_user_all() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            orders = result.scalars().all()
            if not orders:
                logger.warning(f"No order found for user: {username}")
                return None

            return orders

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_user_all()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_user_all()", f"Error: {e}")


# 選択（一般ユーザー:指定日）
@log_decorator
async def select_orders_by_user_at_date(username: str, target_date: date) -> Optional[List[Orders]]:
    """
    指定された username と target_date に該当する注文レコードを取得する。
    
    target_date は datetime.date 型で渡し、Orders.created_at がその日付の 00:00:00～23:59:59 の範囲内の注文を対象とする。
    
    戻り値は Orders オブジェクトのリスト（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            start_dt = f"{target_date.isoformat()} 00:00:00"
            end_dt = f"{target_date.isoformat()} 23:59:59"
            
            stmt = select(Orders).where(
                Orders.username == username,
                Orders.created_at.between(start_dt, end_dt)
            )
            logger.debug(f"select_orders_by_user_at_date() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            orders = result.scalars().all()
            if not orders:
                logger.warning(f"No order found for user: {username} on {target_date.isoformat()}")
                return None
            return orders

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_user_at_date()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_user_at_date()", f"Error: {e}")


# 選択（一般ユーザー:日付遡及）
@log_decorator
async def select_orders_by_user_ago(username: str, days_ago: int = 0) -> Optional[List[Orders]]:
    """
    指定された username の注文レコードを、本日から指定日数前（days_ago_str）から本日までの期間に絞り込んで取得する。
    
    例）days_ago_str="3" → 本日から３日前～本日の期間の注文を取得する。
    
    戻り値は Orders オブジェクトのリスト（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 基本クエリ：username でフィルタ
            stmt = select(Orders).where(Orders.username == username)

            # 例: days_ago日前から本日までの期間を取得
            start_dt, end_dt = await get_created_at_period(days_ago)
            stmt = stmt.where(Orders.created_at.between(start_dt, end_dt))
            # days_ago が指定されている場合、期間条件を追加
            '''if days_ago:
                start_day = get_today_str(days_ago, "YMD")
                end_day = get_today_str(0, "YMD")
                # 例："2025-04-04"
                start_dt = f"{start_day} 00:00:00"
                end_dt = f"{end_day} 23:59:59"
                stmt = stmt.where(Orders.created_at.between(start_dt, end_dt))'''
            
            logger.debug(f"select_orders_by_user_ago() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)

            orders = result.scalars().all()
            if not orders:
                logger.warning(f"No order found for user: {username} within the specified period")
                return None

            return orders

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_user_ago()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_user_ago()", f"Error: {e}")

'''-------------------------------------------------------------'''
from .company import Company
from .menu import Menu

# 選択（会社発注者:全件）
@log_decorator
async def select_orders_by_company_all(company_id: int) -> Optional[List[Orders]]:
    """
    指定されたcompany_idの注文レコードを、CompanyおよびMenu情報と結合して取得する。
    戻り値は Order オブジェクトのリスト（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    Orders.order_id,
                    Company.name.label("company_name"),
                    Orders.username,
                    Orders.shop_name,
                    Menu.name.label("menu_name"),
                    Orders.amount,
                    Orders.created_at,
                    Orders.canceled
                )
                .select_from(Orders)
                .join(Company, Orders.company_id == Company.company_id)
                .join(Menu, Orders.menu_id == Menu.menu_id)
                .where(Orders.company_id == company_id)
            )

            logger.debug(f"select_orders_by_company_all() - SQLAlchemyクエリ: {stmt}")

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning("No order found for the given company_id")
                return None

            order_list: List[Orders] = []
            for row in rows:
                # SQLAlchemyの Row オブジェクトは _mapping 属性で辞書のようにアクセス可能
                row_dict = dict(row._mapping)
                order_list.append(Orders(**row_dict))

            logger.debug(f"select_orders_by_company_all() - order_list: {order_list}")
            return order_list

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_company()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_company()", f"Error: {e}")


# 選択（会社発注者：指定日）
@log_decorator
async def select_orders_by_company_at_date(company_id: int, target_date: date) -> Optional[List[Orders]]:
    """
    指定された company_id と target_date に該当する注文レコードを、
    Company および Menu 情報と結合して取得する。
    
    target_date は datetime.date 型で渡し、Orders.created_at がその日付の
    00:00:00～23:59:59 の範囲内の注文を対象とする。
    
    戻り値は Order オブジェクトのリスト（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            # target_date を文字列に変換して期間を作成
            start_datetime = f"{target_date.isoformat()} 00:00:00"
            end_datetime   = f"{target_date.isoformat()} 23:59:59"
            
            stmt = (
                select(
                    Orders.order_id,
                    Company.name.label("company_name"),
                    Orders.username,
                    Orders.shop_name,
                    Menu.name.label("menu_name"),
                    Orders.amount,
                    Orders.created_at,
                    Orders.canceled
                )
                .select_from(Orders)
                .join(Company, Orders.company_id == Company.company_id)
                .join(Menu, Orders.menu_id == Menu.menu_id)
                .where(Orders.company_id == company_id)
                .where(Orders.created_at.between(start_datetime, end_datetime))
            )
            
            logger.debug(f"select_orders_by_company_at_date() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning("No order found for the given company_id and target_date")
                return None
            
            order_list: List[Orders] = []
            for row in rows:
                # SQLAlchemy の Row オブジェクトは _mapping 属性で辞書としてアクセス可能
                row_dict = dict(row._mapping)
                order_list.append(Orders(**row_dict))
            
            logger.debug(f"select_orders_by_company_at_date() - order_list: {order_list}")
            return order_list

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_company_at_date()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_company_at_date()", f"Error: {e}")


# 選択（会社発注者:日付遡及）
@log_decorator
async def select_orders_by_company_ago(company_id: int, days_ago: int = 0) -> Optional[List[Orders]]:
    """
    指定されたcompany_idの注文レコードを、CompanyおよびMenu情報と結合して取得する。
    days_ago_strが指定されている場合、created_atが指定期間内の注文に絞り込む。
    戻り値は Order オブジェクトのリスト（存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            # ベースとなるクエリの作成
            stmt = (
                select(
                    Orders.order_id,
                    Company.name.label("company_name"),
                    Orders.username,
                    Orders.shop_name,
                    Menu.name.label("menu_name"),
                    Orders.amount,
                    Orders.created_at,
                    Orders.canceled
                )
                .select_from(Orders)
                .join(Company, Orders.company_id == Company.company_id)
                .join(Menu, Orders.menu_id == Menu.menu_id)
                .where(Orders.company_id == company_id)
            )
            
            # 期間指定がある場合、created_atの条件を追加
            stmt = select(Orders).where(Orders.company_id == company_id)
            # 例: days_ago日前から本日までの期間を取得
            start_dt, end_dt = await get_created_at_period(days_ago)
            stmt = stmt.where(Orders.created_at.between(start_dt, end_dt))
            '''if days_ago:
                start_day = get_today_str(days_ago, "YMD")
                end_day = get_today_str(0, "YMD")
                start_datetime = f"{start_day} 00:00:00"
                end_datetime = f"{end_day} 23:59:59"
                stmt = stmt.where(Orders.created_at.between(start_datetime, end_datetime))'''
            
            logger.debug(f"select_orders_by_company_ago() - SQLAlchemyクエリ: {stmt}")
            
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning("No order found for the given company_id")
                return None
            
            # 各行を辞書に変換し、Orderオブジェクトを生成（appendOrder()相当の処理）
            order_list: List[Orders] = []
            for row in rows:
                # SQLAlchemyのRowは _mapping 属性で辞書風にアクセス可能
                row_dict = dict(row._mapping)
                order_list.append(Orders(**row_dict))
            
            logger.debug(f"select_orders_by_company_ago() - order_list: {order_list}")
            return order_list

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_company_ago()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_company_ago()", f"Error: {e}")
'''-------------------------------------------------------------'''
# 選択（店舗:全件）
@log_decorator
async def select_orders_by_shop_all(shop_name: str) -> Optional[List[Orders]]:
    """
    指定された shop_name に該当する全注文情報を、
    Company および Menu テーブルと結合して取得する。
    戻り値は Orders オブジェクトのリストとして返す（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    Orders.order_id,
                    Company.name.label("company_name"),
                    Orders.username,
                    Orders.shop_name,
                    Menu.name.label("menu_name"),
                    Orders.amount,
                    Orders.created_at,
                    Orders.canceled
                )
                .select_from(Orders)
                .join(Company, Orders.company_id == Company.company_id)
                .join(Menu, Orders.menu_id == Menu.menu_id)
                .where(Orders.shop_name == shop_name)
            )
            logger.debug(f"select_orders_by_shop_all() - SQLAlchemyクエリ: {stmt}")
            
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found with the given shop_name: {shop_name}")
                return None
            
            order_list: List[Orders] = []
            for row in rows:
                row_dict = dict(row._mapping)
                # 必要に応じた型変換
                row_dict["order_id"] = int(row_dict["order_id"])
                row_dict["amount"] = int(row_dict["amount"])
                row_dict["canceled"] = bool(row_dict["canceled"])
                order_list.append(Orders(**row_dict))
            
            logger.debug(f"select_orders_by_shop_all() - order_list: {order_list}")
            return order_list

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_shop_all()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_shop_all()", f"Error: {e}")


# 選択（店舗:会社指定）
@log_decorator
async def select_orders_by_shop_company(shop_name: str, company_id: int) -> Optional[List[Orders]]:
    """
    指定された shop_name と company_id に該当する注文情報を、
    Company および Menu テーブルと結合して取得する。
    取得結果は Orders オブジェクトのリストとして返す（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    Orders.order_id,
                    Company.name.label("company_name"),
                    Orders.username,
                    Orders.shop_name,
                    Menu.name.label("menu_name"),
                    Orders.amount,
                    Orders.created_at,
                    Orders.canceled
                )
                .select_from(Orders)
                .join(Company, Orders.company_id == Company.company_id)
                .join(Menu, Orders.menu_id == Menu.menu_id)
                .where(Orders.shop_name == shop_name, Orders.company_id == company_id)
            )
            logger.debug(f"select_orders_by_shop_company() - SQLAlchemyクエリ: {stmt}")
            
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning(f"No order found for shop: {shop_name} and company_id: {company_id}")
                return None
            
            order_list: List[Orders] = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["order_id"] = int(row_dict["order_id"])
                row_dict["amount"] = int(row_dict["amount"])
                row_dict["canceled"] = bool(row_dict["canceled"])
                order_list.append(Orders(**row_dict))
            
            logger.debug(f"select_orders_by_shop_company() - order_list: {order_list}")
            return order_list

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_shop_company()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_shop_company()", f"Error: {e}")


# 選択（店舗：指定日）
@log_decorator
async def select_orders_by_shop_at_date(shop_name: str, target_date: date) -> Optional[List[Orders]]:
    """
    指定された shop_name と target_date に該当する注文レコードを、Company および Menu 情報と結合して取得する。
    
    target_date は datetime.date 型で渡し、Orders.created_at がその日付の 00:00:00～23:59:59 の範囲内の注文を対象とする。
    
    戻り値は Orders オブジェクトのリスト（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            # target_date を文字列に変換して、期間を作成
            start_datetime = f"{target_date.isoformat()} 00:00:00"
            end_datetime = f"{target_date.isoformat()} 23:59:59"
            
            stmt = (
                select(
                    Orders.order_id,
                    Company.name.label("company_name"),
                    Orders.username,
                    Orders.shop_name,
                    Menu.name.label("menu_name"),
                    Orders.amount,
                    Orders.created_at,
                    Orders.canceled
                )
                .select_from(Orders)
                .join(Company, Orders.company_id == Company.company_id)
                .join(Menu, Orders.menu_id == Menu.menu_id)
                .where(Orders.shop_name == shop_name)
                .where(Orders.created_at.between(start_datetime, end_datetime))
            )
            
            logger.debug(f"select_orders_by_shop_at_date() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning("No order found for the given shop_name and target_date")
                return None

            order_list: List[Orders] = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["order_id"] = int(row_dict["order_id"])
                row_dict["amount"] = int(row_dict["amount"])
                row_dict["canceled"] = bool(row_dict["canceled"])
                order_list.append(Orders(**row_dict))
            
            logger.debug(f"select_orders_by_shop_at_date() - order_list: {order_list}")
            return order_list

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_shop_at_date()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_shop_at_date()", f"Error: {e}")


# 選択（店舗:日付遡及）
@log_decorator
async def select_orders_by_shop_ago(shop_name: str, days_ago: int = 0) -> Optional[List[Orders]]:
    """
    指定された shop_name の注文レコードを、Company および Menu 情報と結合して取得する。
    days_ago_str が指定されている場合、本日から指定日数前（例："3" → 3日前）の開始日から今日までの
    Orders.created_at の範囲内の注文に絞り込む。
    
    戻り値は Orders オブジェクトのリスト（注文が存在しなければ None）。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 基本クエリの構築（内部結合で Company, Menu の情報も取得）
            stmt = (
                select(
                    Orders.order_id,
                    Company.name.label("company_name"),
                    Orders.username,
                    Orders.shop_name,
                    Menu.name.label("menu_name"),
                    Orders.amount,
                    Orders.created_at,
                    Orders.canceled
                )
                .select_from(Orders)
                .join(Company, Orders.company_id == Company.company_id)
                .join(Menu, Orders.menu_id == Menu.menu_id)
                .where(Orders.shop_name == shop_name)
            )

            # days_ago_str が指定されている場合、開始日と終了日（本日）を生成して期間条件を追加
            stmt = select(Orders).where(Orders.username == shop_name)
            # 例: days_ago日前から本日までの期間を取得
            start_dt, end_dt = await get_created_at_period(days_ago)
            stmt = stmt.where(Orders.created_at.between(start_dt, end_dt))
            '''if days_ago:
                start_day = get_today_str(days_ago, "YMD")
                # 例："2025-04-01"（days_ago=3 なら本日が2025-04-04の場合）
                end_day = get_today_str(0, "YMD")             # 本日（例："2025-04-04"）
                start_datetime = f"{start_day} 00:00:00"
                end_datetime = f"{end_day} 23:59:59"
                stmt = stmt.where(Orders.created_at.between(start_datetime, end_datetime))'''
            
            logger.debug(f"select_orders_by_shop_ago() - SQLAlchemyクエリ: {stmt}")
            result = await session.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.warning("No order found for the given shop_name with the specified period")
                return None
            
            order_list: List[Orders] = []
            for row in rows:
                row_dict = dict(row._mapping)
                # 必要に応じた型変換
                row_dict["order_id"] = int(row_dict["order_id"])
                row_dict["amount"] = int(row_dict["amount"])
                row_dict["canceled"] = bool(row_dict["canceled"])
                order_list.append(Orders(**row_dict))
            
            logger.debug(f"select_orders_by_shop_ago() - order_list: {order_list}")
            return order_list

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_orders_by_shop_ago()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_orders_by_shop_ago()", f"Error: {e}")

'''-------------------------------------------------------------'''
# 追加
@log_decorator
async def insert_order(
    company_id: int,
    username: str,
    shop_name: str,
    menu_id: int,
    amount: int,
    created_at: Optional[str] = None) -> int:
    """
    Ordersテーブルに新規注文を挿入する関数です。
    created_atがNoneの場合は、get_today_str()で生成した値を設定します。
    挿入後、新規レコードの order_id を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            # created_atがNoneの場合、デフォルト値を設定
            created_at = created_at if created_at else get_today_str()
            logger.debug(f"insert_order() called with created_at = {created_at}")

            # Orderモデルの新規インスタンスを生成
            new_order = Orders(
                company_id=company_id,
                username=username,
                shop_name=shop_name,
                menu_id=menu_id,
                amount=amount,
                created_at=created_at
            )
            session.add(new_order)
            await session.commit()
            # 挿入後、refreshして自動採番された主キーを取得
            await session.refresh(new_order)
            order_id = new_order.order_id

            logger.info("注文追加成功")
            logger.debug(f"insert_order() - 新規注文の値: {(company_id, username, shop_name, menu_id, amount, created_at)}")
            order_logger("ORDER", f"注文完了 - order_id:{order_id} - {company_id}:{username}, {shop_name}:{menu_id}, {amount}")
            return order_id

    except DatabaseError as e:
        raise SQLException(
            sql_statement="INSERT INTO Orders ...",
            method_name="insert_order()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "insert_order()", f"Error: {e}")

'''-------------------------------------------------------------'''
# 更新
from sqlalchemy import update
from utils.utils import get_today_str

@log_decorator
async def update_order(order_id: int, canceled: bool):
    """
    指定された order_id の注文レコードに対して、canceled フラグと updated_at を更新します。
    """
    try:
        async with AsyncSessionLocal() as session:
            current_time = get_today_str()
            stmt = (
                update(Orders)
                .where(Orders.order_id == order_id)
                .values(canceled=canceled, updated_at=current_time)
            )
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                logger.warning(f"注文更新失敗: order_id {order_id} の注文が見つかりませんでした。")
            else:
                logger.info(f"注文更新成功: order_id {order_id}")
            logger.debug(f"update_order() - SQL: {stmt}")

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="update_order()",
            detail=f"SQL実行中にエラーが発生しました: {e}",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "update_order()", f"Error: {e}")
'''-------------------------------------------------------------'''
from sqlalchemy import text

# 削除（指定ID）
from sqlalchemy import delete, text
from sqlalchemy.exc import DatabaseError

@log_decorator
async def delete_order(order_id: int) -> bool:
    """
    指定された order_id の Order レコードを削除します。
    削除対象が存在しなければ False を返し、削除に成功すれば True を返します。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(Orders).where(Orders.order_id == order_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                logger.warning(f"Order with order_id {order_id} not found.")
                return False

            logger.info(f"Order with order_id {order_id} deleted successfully.")
            return True

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="delete_order()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "delete_order()", f"Error: {e}")


# 削除（全件）
@log_decorator
async def delete_all_orders():
    sqlstr = "DROP TABLE IF EXISTS orders"
    try:
        def drop_table(sync_conn):
            sync_conn.execute(text(sqlstr))

        async with AsyncSessionLocal() as session:
            await session.run_sync(drop_table)
    except DatabaseError as e:
        raise SQLException(
            sql_statement=sqlstr,
            method_name="delete_all_orders()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "delete_all_orders()", f"Error: {e}")
