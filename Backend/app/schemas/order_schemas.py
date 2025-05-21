# schemas/order_schemas.py
# pydantic用クラス
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class OrderModel(BaseModel):
        order_id: int
        company_name: str
        username: str
        shop_name: str
        menu_name: str
        amount: int
        created_at: Optional[datetime] = None
        updated_at: Optional[datetime] = None
        expected_delivery_date: Optional[datetime] = None
        checked: Optional[bool] = None

from pydantic import BaseModel
from typing import List

class OrderUpdate(BaseModel):
    order_id: int
    checked: bool

class OrderUpdateList(BaseModel):
    updates: List[OrderUpdate]

