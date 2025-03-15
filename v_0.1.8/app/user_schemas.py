# user_schemas.py
# pydantic用クラス
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class UserBase(BaseModel):
    username: str
    name: Optional[str] = None
    company_id: Optional[int] = None
    shop_name: Optional[str] = None
    menu_id: Optional[int] = None
    permission: Optional[int] = 1

    class Config:
        from_attributes = True  # ここに設定することで全ての派生クラスに適用される
    
    '''
    使用例
    user = UserBase(username="alice", company_id=123, shop_name="Shop A")
    '''
    # ゲッターメソッド
    def get_username(self) -> str:
        return self.username

    def get_name(self) -> Optional[str]:
        return self.name

    def get_company_id(self) -> Optional[int]:
        return self.company_id

    def get_shop_name(self) -> Optional[str]:
        return self.shop_name

    def get_menu_id(self) -> Optional[int]:
        return self.menu_id

    def get_permission(self) -> Optional[int]:
        return self.permission


class UserCreate(UserBase):
    _password: str = PrivateAttr()

    def __init__(self, **data):
        password = data.pop("password")
        super().__init__(**data)
        self._password = password

    def get_password(self) -> str:
        return self._password


class UserResponse(UserBase):
    user_id: int
    token: Optional[str] = None
    exp: Optional[str] = None
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())

    ''' 使用例
        user_response = UserResponse(
                username="bob",
                user_id=42,
                token="abcdef12345",
                exp="2025-12-31T23:59:59",
                updated_at=datetime(2025, 3, 13, 12, 0, 0)
        )
    '''
    # ゲッターメソッド
    def get_user_id(self) -> int:
        return self.user_id

    def get_token(self) -> Optional[str]:
        return self.token

    def get_exp(self) -> Optional[str]:
        return self.exp

    def get_updated_at(self) -> Optional[datetime]:
        return self.updated_at




