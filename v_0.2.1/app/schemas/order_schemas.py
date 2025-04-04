# order_schemas.py
# pydantic用クラス
from dataclasses import Field
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, PrivateAttr, RootModel
from typing import Optional


class Order(BaseModel):
        order_id: int
        company_name: str
        username: str
        shop_name: str
        menu_name: str
        amount: int
        created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
        canceled: Optional[bool] = Field(default=False)

        def get_created_at(self) -> datetime:
                print(f"order_id: {self.created_at}, created_at: {self.created_at}")
                return self.created_at

        def get_end_of_today(self) -> datetime:
                # 期限として本日の23:59:59を作成
                today = datetime.now()
                end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
                print(f"order_id: {self.created_at}, end_of_day: {end_of_day}")
                return end_of_day
