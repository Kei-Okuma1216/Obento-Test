# schemas/order_schemas.py
# pydantic用クラス
from dataclasses import Field
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class OrderModel(BaseModel):
        order_id: int
        company_name: str
        username: str
        shop_name: str
        menu_name: str
        amount: int
        created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
        expected_delivery_date: Optional[datetime] = Field(default=None)
        checked: Optional[bool] = Field(default=False)

        def get_created_at(self) -> datetime:
                print(f"order_id: {self.created_at}, created_at: {self.created_at}")
                return self.created_at

        def get_end_of_today(self) -> datetime:
                # 期限として本日の23:59:59を作成
                today = datetime.now()
                end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
                print(f"order_id: {self.created_at}, end_of_day: {end_of_day}")
                return end_of_day

from pydantic import BaseModel
from typing import List

class OrderUpdate(BaseModel):
    order_id: int
    checked: bool

class OrderUpdateList(BaseModel):
    updates: List[OrderUpdate]

