# パスパラメータ
# https://fastapi.tiangolo.com/ja/tutorial/path-params-numeric-validations/
from typing import List, Union
from uuid import UUID
from fastapi import Body, FastAPI, Path, Query
from pydantic import BaseModel, Field
from datetime import datetime, time, timedelta

class Image(BaseModel):
    url: str
    name: str
    
class Item(BaseModel):
    name: str
    description: Union[str, None] = Field(
        default=None, title="The description of the item", max_length=300
    )
    price: float = Field(
        gt=0, description="The price must be greater than zero")
    tax: Union[float, None] = None
    tags: List[str] = []
    image: Union[Image, None] = None
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                }
            ]
        }
    }

class User(BaseModel):
    username: str
    full_name: Union[str, None] = None

app = FastAPI()

@app.put("/items/{item_id}")
async def read_items(
    item_id: UUID,
    start_datetime: datetime = Body(),
    end_datetime: datetime = Body(),
    process_after: timedelta = Body(),
    repeat_at: Union[time, None] = Body(default=None),
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }
'''
curl -X PUT "http://127.0.0.1:8000/items/123e4567-e89b-12d3-a456-426614174000" -H "Content-Type: application/json" -d @data.json
{
  "_comment": "改行は Shift + Alt + F",
  "start_datetime": "2025-01-16T10:00:00Z",
  "end_datetime": "2025-01-16T12:00:00Z",
  "process_after": 3600,
  "repeat_at": "10:30:00"
}
'''

'''
@app.put("/items/{item_id}")
async def update_item(
    *,
    item_id: int,
    item: Item,
    user: User,
    importance: int = Body(gt=0),
    q: Union[str, None] = None,
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    if q:
        results.update({"q": q})
    return results

@app.get("/items/{item_id}")
async def read_items(
    q: str, item_id: int = Path(title="The ID of the item to get", gt=0, le=1000),
    size: float = Query(gt=0, lt=10.5)):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if size:
        results.update({"size": size})
    return results
'''
# ブラウザではGETになりエラーになる
# POST確認は別ターミナルで実行する
# curl -X POST "http://127.0.0.1:8000/items/" -H "Content-Type: application/json" -d "{\"name\": \"Sample Item\", \"description\": \"This is a sample item.\", \"price\": 10.0, \"tax\": 0.5}"


