# schemas/menu_schemas.py
# pydantic用クラス
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class MenuModel(BaseModel):
    menu_id: int
    shop_name: str
    name: str
    price: int
    description: Optional[str] = None
    picture_path: Optional[str] = None
    disabled: Optional[bool] = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())

    class Config:
        from_attributes = True  # ここに設定することで全ての派生クラスに適用される

