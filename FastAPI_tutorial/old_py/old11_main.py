# 備考
# ここで共通のクエリクラスを作って、依存性注入で渡すことができる
from typing import Union

from fastapi import Depends, FastAPI

app = FastAPI()
# 依存関係 - 最初のステップ
# https://fastapi.tiangolo.com/ja/tutorial/dependencies/classes-as-dependencies/#_3

# item db
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

# クエリ専用クラス
class CommonQueryParams:
    def __init__(self, q: Union[str, None] = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

'''
async def common_parameters(
    q: Union[str, None] = None, skip: int = 0, limit: int = 100
):
    return {"q": q, "skip": skip, "limit": limit}
'''

@app.get("/items/")
#async def read_items(commons: dict = Depends
#(common_parameters)):
async def read_items(
    #commons: CommonQueryParams = Depends(CommonQueryParams)):
    commons: CommonQueryParams = Depends()):
    #return commons
    response = {}
    if commons.q:
        response.update({"q": commons.q})
    items = fake_items_db[commons.skip : commons.skip + commons.limit]
    response.update({"items": items})
    return response


@app.get("/users/")
async def read_users(
    #commons: dict = Depends(common_parameters)):
    commons: CommonQueryParams = Depends(CommonQueryParams)):
    return commons

class Cat:
    def __init__(self, name: str):
        self.name = name


fluffy = Cat(name="Mr Fluffy")