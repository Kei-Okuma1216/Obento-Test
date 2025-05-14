# schemas/company_schemas.py
# pydantic用クラス
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class CompanyModel(BaseModel):
    company_id: int
    name: str
    tel: Optional[str] = None
    shop_name: Optional[str] = None
    # created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # is_modified: Optional[bool] = Field(default=False)
    is_modified: Optional[bool] = None

    class Config:
        from_attributes = True  # ここに設定することで全ての派生クラスに適用される