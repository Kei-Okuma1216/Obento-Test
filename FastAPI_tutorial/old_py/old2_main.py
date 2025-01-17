from typing import List, Union

from fastapi import FastAPI, Query
from pydantic import BaseModel

# 
# https://fastapi.tiangolo.com/ja/tutorial/body/#pydantic-basemodel

class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None
    
# uvicorn main:app --reload
app = FastAPI()


# 複数回出現するq
# 例 http://localhost:8000/items/?q=foo&q=bar
@app.get("/items/")
async def read_items(q: Union[List[str], None] = Query(default=None)):
    query_items = {"q": q}
    return query_items

# qの引数を50文字に制限
'''
@app.get("/items/")
async def read_items(q: Union[str, None] 
    = Query(default=None, min_length=3, max_length=50, pattern="^fixedquery$")):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results
'''

# 追加
# curl -X POST "http://127.0.0.1:8000/items/" -H "Content-Type: application/json" -d "{\"name\": \"Sample Item\", \"description\": \"This is a sample item.\", \"price\": 10.0, \"tax\": 0.5}"
@app.post("/items/")
async def create_item(item: Item):
    print(item)
    item_dict = item.model_dump() # model_dumpを使用
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict

# 更新
# curl -X PUT "http://127.0.0.1:8000/items/1" -H "Content-Type: application/json" -d "{\"name\": \"Updated Item\", \"description\": \"This is an updated item.\", \"price\": 15.0, \"tax\": 1.0}"
'''@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dic.model_dump()}
'''

# curl -X POST "http://127.0.0.1:8000/items/2?q=bar" -H "Content-Type: application/json" -d "{\"name\": \"Sample Item\", \"description\": \"This is a sample item.\", \"price\": 10.0, \"tax\": 0.5}"
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: Union[str, None] = None):
    result = {"item_id": item_id, **item.dict()}
    if q:
        result.update({"q": q})
    return result
# ブラウザではGETになりエラーになる
# POST確認は別ターミナルで実行する
# curl -X POST "http://127.0.0.1:8000/items/" -H "Content-Type: application/json" -d "{\"name\": \"Sample Item\", \"description\": \"This is a sample item.\", \"price\": 10.0, \"tax\": 0.5}"


