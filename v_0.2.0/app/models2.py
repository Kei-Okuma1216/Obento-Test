from sqlalchemy import Base, String, Boolean, DateTime, Integer, Column, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemyのベースクラスを作成
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    token = Column(String, nullable=True)
    exp = Column(String, nullable=True)
    shop_id = Column(Integer, nullable=True)
    menu_id = Column(Integer, nullable=True)
    permission = Column(Integer, default=1)
    is_modified = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.now())
    orders = relationship("OrderDB", back_populates="user")

class Order(Base):
    __tablename__ = 'order'
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    shop_id = Column(Integer, nullable=True)
    menu_id = Column(Integer, nullable=True)
    count = Column(Integer, default=1)
    is_checked = Column(Boolean, default=False)
    is_canceled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, nullable=True)
    users = relationship("UserDB", back_populates="order")

class Company(Base):
    __tablename__ = 'company'
    company_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    tel = Column(String, nullable=True)
    shop_id = Column(Integer, nullable=True)
    menu_id = Column(Integer, nullable=True)
    is_disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, nullable=True)
    users = relationship("UserDB", back_populates="company")

class Shop(Base):
    __tablename__ = 'shop'
    shop_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    tel = Column(String, nullable=True)
    fax = Column(String, nullable=True)
    is_disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    menus = relationship("MenuDB", back_populates="shop")

class Menu(Base):
    __tablename__ = 'menu'
    menu_id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    is_disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())    
    shops = relationship("ShopDB", back_populates="menu")
