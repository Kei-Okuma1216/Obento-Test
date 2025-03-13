# models.py
from dataclasses import Field
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, RootModel
from typing import Optional
'''
Orderクラス
使用方法
# 1. List[dict]をjsonにする
        json_data = json.dumps(o, ensure_ascii=False)
        #print(f"json_data: {json_data}")
# 2. JSON文字列をpython辞書に変換
        dict_data = json.loads(json_data)
# 3. python辞書をOrderクラスに変換する  
        orderlist.append(Order(**dict_data))
# 4. Orderオブジェクトを辞書に変換
        orders_dict = [order.dict() for order in orders]
# 5. 辞書リストをJSON文字列に変換
        orders_json = json.dumps(orders_dict, indent=4, default=str)
# 6.JSONを出力
        print(orders_json)
# 99. ordersリストを降順にソート
        orders.sort(key=lambda x: x.created_at, reverse=True)
'''
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

class Orders(RootModel[list[Order]]):
    def sort_by_desc(self):
        print(f"*****This is a custom method with root: {self.root}")

class Payload(BaseModel):
    sub: str
    token: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    exp: Optional[datetime] = Field(default_factory=lambda: Payload.get_expire_datetime())
    
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
    def create(cls, payload) -> 'Payload':
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
    


class User(BaseModel):
    user_id: int
    username: str
    password: str
    name: Optional[str] = None
    token: Optional[str] = None
    exp: Optional[str] = None
    company_id: Optional[int] = None
    shop_name: Optional[str] = Field(default=1)
    menu_id: Optional[int] = None
    permission: Optional[int] = Field(default=1)
    is_modified: Optional[bool] = Field(default=False)
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())

    '''@classmethod
    def create_user(cls, user_id: int, username: str, password: str, name: str) -> 'User':
        return cls(id=id, password=password, name=name)
    '''
    def get_user_id(self) -> int:
            return self.user_id
    
    def get_username(self) -> str:
        return self.username

    def get_password(self):
        return self.password
    
    def get_name(self) -> str:
            return self.name

    def set_name(self, name):
        self.name = name

    def get_token(self) -> str:
            return self.token

    def get_exp(self) -> int:
        return self.exp
        
    def get_company_id(self) -> int:
            return self.company_id

    def get_shop_name(self) -> str:
            return self.shop_name
    
    def get_menu_id(self) -> int:
            return self.menu_id
        
    def get_permission(self) -> int:
            return self.permission
    
    def get_updated_at(self) -> str:
            return self.updated_at

    def to_str(self) -> str:
        return self.updated_at.strftime("%Y-%m-%d") if self.updated_at else "No date set"

    def get_date(self, add_days: int = 0) -> datetime:
        new_date = datetime.now() + datetime.timedelta(days=add_days)
        return new_date

    def get_now(self, add_days: int = 0) -> datetime:
        new_date = datetime.now() + datetime.timedelta(days=add_days)
        return new_date#new_date.strftime("%Y-%m-%d %H:%M")

    def to_date_str(self, dt: datetime) -> 'User':
        # 例: 2025-01-23
        self.datetime_str = dt.strftime("%Y-%m-%d")
        return self if self.dt else "No date set"

    def to_datetime_str(self, dt: datetime) -> 'User':
        # 例: 2025-01-23 10:34
        self.datetime_str = dt.strftime("%Y-%m-%d %H:%M")
        return self if self.dt else "No date set"

    def set_is_modified(self):
        self.is_modified = True 


    def set_token(self,token: str):
        self.token = token

    def set_exp(self, exp: str):
        self.exp = exp

    def set_max_age(self, max_age: str):
        self.exp = max_age
        
    #def get_max_age_str(self) -> str:
    #    return convert_max_age_to_dhms(self.exp)
        
    #def print_max_age_str(self) -> str:
    #    day, hour, minute, second = convert_max_age_to_dhms(self.exp)
    #    print(f"{day}日, {hour}時間, {minute}分, {second}秒 ")

'''修正後の schemas.py'''
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

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    user_id: int
    token: Optional[str] = None
    exp: Optional[str] = None
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())





