# models/company.py
'''
    class Company(Base):
    create_company_table():
    select_company(company_id: int):
    select_all_company():
    insert_company(name: str, tel: str, shop_name: str):
    update_company(company_id: int, key: str, value: str):
    delete_company(company_id: int):
'''
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base
Base = declarative_base()

from sqlalchemy.exc import DatabaseError

class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tel = Column(String, nullable=True)
    shop_name = Column(String, nullable=True)
    created_at = Column(String, nullable=True)
    disabled = Column(Boolean, default=False)
    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

from utils.utils import log_decorator
from utils.exception import SQLException, CustomException
from database import async_session, async_engine


import logging
logger = logging.getLogger(__name__)


# 作成
@log_decorator
async def create_company_table():
    """
    Companyテーブルの作成（存在しなければ）
    ※通常、テーブル作成はマイグレーションツール（Alembic等）で行いますが、
      ここでは例としてSQLAlchemyのメタデータからテーブル作成する方法を示します。
    """
    try:
        async with async_engine.begin() as conn:
            # Companyテーブルを存在チェック付きで作成
            await conn.run_sync(Company.__table__.create, checkfirst=True)
        logger.info("Companyテーブルの作成に成功（既に存在する場合は作成されません）")
    except DatabaseError as e:
        raise SQLException(
            sql_statement="CREATE TABLE Company",
            method_name="create_company_table()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "create_company_table()", f"Error: {e}")


from sqlalchemy import select, update, delete


# 取得(1件)
@log_decorator
async def select_company(company_id: int):
    """
    指定されたcompany_idのCompanyレコードを取得する
    """
    try:
        async with async_session() as session:
            stmt = select(Company).where(Company.company_id == company_id)
            result = await session.execute(stmt)
            company = result.scalar_one_or_none()

            logger.debug(f"select_company() - {stmt}")
            return company

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_company()", f"Error: {e}")

# 取得（全件）
@log_decorator
async def select_all_company():
    """
    全てのCompanyレコードを取得する
    """
    try:
        async with async_session() as session:
            stmt = select(Company)
            result = await session.execute(stmt)
            companies = result.scalars().all()

            logger.debug(f"select_all_company() - {stmt}")
            return companies

    except DatabaseError as e:
        raise SQLException(
            sql_statement=str(stmt),
            method_name="select_all_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "select_all_company()", f"Error: {e}")


from utils.utils import get_today_str

# 追加
@log_decorator
async def insert_company(name: str, telephone: str, shop_name: str):
    """
    Companyテーブルに新規レコードを追加する
    """
    try:
        async with async_session() as session:
            new_company = Company(
                name=name,
                tel=telephone,
                shop_name=shop_name,
                created_at=get_today_str(),
                disabled=False
            )
            session.add(new_company)
            await session.commit()

            logger.info("契約企業追加成功")
            logger.debug(
                f"insert_company() - name: {name}, tel: {tel}, shop_name: {shop_name}, "
                f"created_at: {get_today_str()}, disabled: False"
            )
            return new_company

    except DatabaseError as e:
        raise SQLException(
            sql_statement="INSERT INTO Company",
            method_name="insert_company()",
            detail="SQL実行中にエラーが発生しました",
            exception=e
        )
    except Exception as e:
        raise CustomException(500, "insert_company()", f"Error: {e}")


# 更新
@log_decorator
async def update_company(company_id: int, key: str, value: str):
    """
    指定されたcompany_idのCompanyレコードの任意のカラム（key）をvalueに更新する
    ※ keyの値は信頼できる入力である前提です。
    """
    try:
        async with async_session() as session:
            stmt = update(Company).where(Company.company_id == company_id).values({key: value})
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
        )
    except Exception as e:
        raise CustomException(500, "update_company()", f"Error: {e}")


# 削除
@log_decorator
async def delete_company(company_id: int):
    """
    指定されたcompany_idのCompanyレコードを削除する
    """
    try:
        async with async_session() as session:
            stmt = delete(Company).where(Company.company_id == company_id)
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
        )
    except Exception as e:
        raise CustomException(500, "delete_company()", f"Error: {e}")
