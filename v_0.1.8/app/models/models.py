# models.py
# SQLAlchemy用クラス
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

import datetime

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String(255))
    name = Column(String, nullable=True)
    token = Column(String, nullable=True)
    exp = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=True)
    shop_name = Column(String, nullable=True)
    menu_id = Column(Integer, nullable=True)
    permission = Column(Integer, default=1)
    is_modified = Column(Boolean, default=False)
    updated_at = Column(String, nullable=True)
    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


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

class Orders(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    menu_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="pending")  # 例: pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    user = relationship("User", backref="orders")
    company = relationship("Company", backref="orders")

    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
'''
from sqlalchemy.orm import Session
from models import Orders, User, Company

def create_order(db: Session, user_id: int, company_id: int, menu_id: int, quantity: int, total_price: float):
    new_order = Orders(
        user_id=user_id,
        company_id=company_id,
        menu_id=menu_id,
        quantity=quantity,
        total_price=total_price
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

# 例:
# order = create_order(db, user_id=1, company_id=2, menu_id=5, quantity=2, total_price=30.0)
# print(order.as_dict())
'''


class Menu(Base):
    __tablename__ = "menu"

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
'''
from sqlalchemy.orm import Session
from models import Menu

def create_menu(db: Session, shop_name: str, name: str, price: int, description: str = "", picture_path: str = ""):
    new_menu = Menu(
        shop_name=shop_name,
        name=name,
        price=price,
        description=description,
        picture_path=picture_path
    )
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    return new_menu

# 例:
# menu = create_menu(db, shop_name="Sushi Place", name="Salmon Roll", price=12)
# print(menu.as_dict())
'''



class Device(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(String, nullable=True)  # タグID
    user_id = Column(String, nullable=True)  # ユーザーID
    created_at = Column(DateTime, default=datetime.utcnow)  # 作成日時
    last_order_at = Column(DateTime, nullable=True)  # 最終注文日時

    def as_dict(self):
        """SQLAlchemyモデルを辞書に変換"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
'''
from sqlalchemy.orm import Session
from models import Device

def create_device(db: Session, tag_id: str, user_id: str):
    new_device = Device(
        tag_id=tag_id,
        user_id=user_id
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device

# 例:
# device = create_device(db, tag_id="123ABC", user_id="42")
# print(device.as_dict())
'''





