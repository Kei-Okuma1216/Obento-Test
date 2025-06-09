# schemas/order_schemas.py
# pydantic用クラス
'''
    1. OrderModel: 注文情報を表すモデル
    2. OrderUpdate: 注文の更新情報を表すモデル
    3. OrderUpdateList: 複数の注文更新情報をまとめるモデル
    4. CancelOrderRequest: 注文キャンセル用リクエストモデル
'''

from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

# 注文情報を表すモデル
class OrderModel(BaseModel):
        order_id: int
        company_name: str
        user_id: int
        username: str
        shop_name: str
        menu_name: str
        amount: int
        created_at: Optional[datetime] = None
        updated_at: Optional[datetime] = None
        expected_delivery_date: Optional[datetime] = None
        checked: Optional[bool] = None
        canceled: Optional[bool] = None

# 注文更新用
class OrderUpdate(BaseModel):
    order_id: int
    checked: bool

class OrderUpdateList(BaseModel):
    updates: List[OrderUpdate]

# 注文キャンセル用
class CancelOrderRequest(BaseModel):
    order_ids: List[int]
    user_id: int  # 必要なら。省略可能にしてもOK
