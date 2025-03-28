from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()
# レスポンスモデル「デコレータ」メソッド
# https://fastapi.tiangolo.com/ja/tutorial/response-model/
class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str | None = None


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
'''password is not returned
curl -X POST "http://127.0.0.1:8000/user/" -H "Content-Type: application/json" -d "{\"username\": \"testuser\", \"password\": \"testpassword\", \"email\": \"testuser@example.com\", \"full_name\": \"Test User\"}"
'''
@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn) -> Any:
    return user


'''
class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Union[str, None] = None
'''
'''password returned
curl -X POST "http://127.0.0.1:8000/user/" -H "Content-Type: application/json" -d "{\"username\": \"testuser\", \"password\": \"testpassword\", \"email\": \"testuser@example.com\", \"full_name\": \"Test User\"}"
'''

# Don't do this in production!
'''
@app.post("/user/")
async def create_user(user: UserIn) -> UserIn:
    return user
'''

# Cookie Parameter Models
# https://fastapi.tiangolo.com/ja/tutorial/cookie-param-models/
'''class Cookies(BaseModel):
    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None

@app.get("/items/")
async def read_items(cookies: Annotated[Cookies, Cookie()]):
    return cookies
'''
# Headerをインポート
# https://fastapi.tiangolo.com/ja/tutorial/header-params/
'''
@app.get("/items/")
async def read_items(user_agent: Union[str, None] = Header(default=None)):
    return {"User-Agent": user_agent}
'''
# クッキーのパラメータ
# https://fastapi.tiangolo.com/ja/tutorial/cookie-params/
'''
@app.get("/items/")
async def read_items(ads_id: Union[str, None] = Cookie(default=None)):
    return {"ads_id": ads_id}
'''