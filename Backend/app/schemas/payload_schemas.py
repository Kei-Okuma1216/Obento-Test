# schemas/payload_schemas.py
from datetime import datetime, timedelta
from typing import Optional, Field

from pydantic import BaseModel


class PayloadModel(BaseModel):
    sub: str
    token: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    exp: Optional[datetime] = Field(default_factory=lambda: PayloadModel.get_expire_datetime())
    
    def get_sub(self) -> str:
            print(f" sub: {self.token}")
            return self.sub
    def get_token(self) -> str:
            print(f" token: {self.token}")
            return self.token
    def get_at_created(self) -> datetime:
            print(f" at_created: {self.at_created}")
            return self.at_created
    def get_exp(self) -> datetime:
            print(f" exp: {self.exp}")
            return str(self.exp)
    def get_permission(self) -> int:
            print(f" permission: {self.permission}")
            return self.exp
    def check_expired(cls) -> bool:
        exp = cls.get_expire_datetime()
        return exp <= datetime.now()
    def get_exp_str(self) -> str:
            return str(self.get_exp())
    
    @classmethod
    def create(cls, payload) -> 'PayloadModel':
        return cls(sub=payload['sub'], at_created=payload['at_created'], token=payload['token'], exp=payload['exp'])
    

    @staticmethod
    def get_expire_datetime(cls, expires_delta) -> datetime:
        # tokenの有効期限
        expires_delta_15s = timedelta(seconds=15)
        expires_delta_30s = timedelta(seconds=30)
        expires_delta_30m = timedelta(minutes=30)
        expires_delta_1d = timedelta(days=1)
        expires_delta = expires_delta_30m
        if expires_delta:
                expire = datetime.now() + expires_delta
        else:
                expire = datetime.now() + expires_delta_30m
        return expire