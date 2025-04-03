# models/menu.py
from datetime import datetime
from typing import Text
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from database import Base


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