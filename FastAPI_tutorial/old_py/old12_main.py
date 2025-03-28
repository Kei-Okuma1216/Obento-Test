# 備考 
# ここでインスタンスでなく関数注入をしている。
from typing import Union

from fastapi import Cookie, Depends, FastAPI

app = FastAPI()
# サブ依存関係
# https://fastapi.tiangolo.com/ja/tutorial/dependencies/sub-dependencies/#_2



def query_extractor(q: Union[str, None] = None):
    return q


def query_or_cookie_extractor(
    q: str = Depends(query_extractor),
    last_query: Union[str, None] = Cookie(default=None),
):
    if not q:
        return last_query
    return q


@app.get("/items/")
async def read_query(query_or_default: str = Depends(query_or_cookie_extractor)):
    return {"q_or_cookie": query_or_default}