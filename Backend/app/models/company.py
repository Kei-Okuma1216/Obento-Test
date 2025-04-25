# models/company.py
'''
    1. class Company(Base):
    2. create_company_table():

    3. select_company(company_id: int):
    4. select_all_company():

    5. insert_company(name: str, tel: str, default_shop_name: str):
    6. update_company(company_id: int, key: str, value: str):
    7. delete_company(company_id: int):
    8. delete_all_company():
'''

from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.exc import DatabaseError
from database.local_postgresql_database import Base, engine, AsyncSessionLocal

# Companyテーブル
class Company(Base):
    __tablename__ = "Companies"

    company_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tel = Column(String, nullable=True)
    shop_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    disabled = Column(Boolean, default=False)
    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

# SELECT * FROM public."Companies"
# ORDER BY company_id DESC

from utils.utils import log_decorator
from utils.exception import SQLException, CustomException


import logging
logger = logging.getLogger(__name__)


# 作成
# from .sqlalchemy_database import engine


@log_decorator
async def create_company_table():
    """
    Companyテーブルの作成（存在しなければ）
    ※通常、テーブル作成はマイグレーションツール（Alembic等）で行いますが、
      ここでは例としてSQLAlchemyのメタデータからテーブル作成する方法を示します。
    """
    try:
        # AsyncEngineからbegin()を使用して接続を取得し、DDL操作を実行します。
        async with engine.begin() as conn:
            await conn.run_sync(Company.__table__.create, checkfirst=True)
        logger.info("Companyテーブルの作成に成功（既に存在する場合は作成されません）")
    except DatabaseError as e:
        raise SQLException(
            sql_statement="CREATE TABLE Company",
            method_name="create_company_table()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "create_company_table()", f"Error: {e}") from e

from schemas.company_schemas import CompanyModel
from sqlalchemy import select

# 取得(1件)
from typing import Optional


@log_decorator
async def select_company(company_id: int) -> Optional[CompanyModel]:
    """
    指定されたcompany_idのCompanyレコードを取得し、
    CompanyModel型で返却する。
    """
    try:
        async with AsyncSessionLocal() as session:
            # ORMモデルであるCompanyをクエリする
            stmt = select(Company).where(Company.company_id == company_id)
            result = await session.execute(stmt)
            orm_company = result.scalar_one_or_none()

            logger.debug(f"select_company() - {stmt}")
            if orm_company is None:
                return None

            # ORMオブジェクトをPydanticモデルに変換する（Pydantic v2）
            pydantic_company = CompanyModel.model_validate(orm_company)
            return pydantic_company

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "create_company_table()", f"Error: {e}") from e


# 取得（全件）
from typing import List
@log_decorator
async def select_all_company()-> Optional[List[CompanyModel]]:
    """
    全てのCompanyレコードを取得する
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Company)
            result = await session.execute(stmt)
            orm_companies = result.scalars().all()
            logger.debug(f"select_all_company() - {stmt}")

            # 取得したORMオブジェクトをpydanticモデル(CompanyModel)に変換
            if orm_companies:
                companies = [CompanyModel.model_validate(company) for company in orm_companies]
                return companies
            else:
                return None

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_all_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "select_all_company()", f"Error: {e}") from e

from utils.utils import get_today_datetime, get_today_str
from sqlalchemy import func
# 追加
@log_decorator
async def insert_company(company_name: str,
                         telephone: str,
                         default_shop_name: str) -> bool:
    """
    Companyテーブルに新規レコードを追加する
    """
    try:
        async with AsyncSessionLocal() as session:
            # すでに同じ会社名が存在するか確認（重複チェック）
            stmt = select(func.count()).select_from(Company).where(Company.name == company_name)
            result = await session.execute(stmt)
            count = result.scalar()
            logger.debug(f"insert_company() - COUNTクエリ - count: {count}")

            if count > 0:
                logger.info(f"会社名: {company_name} は既に存在します。挿入をスキップします。")
                return False

            print(f"get_today_datetime: {get_today_datetime}")
            # 新規企業レコードの作成
            new_company = Company(
                # company_id は自動採番される前提のため指定しない
                name=company_name,
                tel=telephone,
                shop_name=default_shop_name,
                created_at=get_today_datetime(), #get_today_str(),
                disabled=False
            )
            session.add(new_company)
            await session.commit()

            logger.info("契約企業追加成功")
            logger.debug(
                f"insert_company() - company_name: {company_name}, tel: {telephone}, shop_name: {default_shop_name}, "
                f"created_at: {get_today_datetime()}, disabled: False"
            )
            return True

    except DatabaseError as e:
        raise SQLException(
            sql_statement="INSERT INTO Company",
            method_name="insert_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        logger.error(f"insert_company() - insert_company() Error: {str(e)}")
        # raise CustomException(500, "insert_company()", f"Error: {e}") from e



# 更新
from sqlalchemy import update
@log_decorator
async def update_company(company_id: int, key: str, value: str):
    """
    指定されたcompany_idのCompanyレコードの任意のカラム（key）をvalueに更新する
    ※ keyの値は信頼できる入力である前提です。
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = update(CompanyModel).where(CompanyModel.company_id == company_id).values({key: value})
            await session.execute(stmt)
            await session.commit()

            logger.debug(f"update_company() - {stmt}")
            return True

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="update_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "create_company_table()", f"Error: {e}") from e


# 削除(1件)
from sqlalchemy import delete
@log_decorator
async def delete_company(company_id: int):
    """
    指定されたcompany_idのCompanyレコードを削除する
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(CompanyModel).where(CompanyModel.company_id == company_id)
            await session.execute(stmt)
            await session.commit()

            logger.info(f"Company {company_id} の削除に成功しました。")
            logger.debug(f"delete_company() - {stmt}")
            return True

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="delete_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "create_company_table()", f"Error: {e}") from e

# 削除（全件）
from sqlalchemy import text
@log_decorator
async def delete_all_company():
    sqlstr = "DROP TABLE IF EXISTS Company"
    try:
        def drop_table(sync_conn):
            sync_conn.execute(text(sqlstr))

        async with AsyncSessionLocal() as session:
            await session.run_sync(drop_table)
            logger.info("Compamy テーブルの削除が完了しました。")

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(sqlstr),
            method_name="delete_all_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        ) from e
    except Exception as e:
        raise CustomException(500, "create_company_table()", f"Error: {e}") from e

