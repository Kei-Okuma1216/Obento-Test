from enum import Enum
from typing import Union

from fastapi import FastAPI


class Planet(str, Enum):
    earth = "earth"
    sun = "sun"
    moon = "moon"

from fastapi import FastAPI, Response, Cookie

# uvicorn main:app --reload
app = FastAPI()

# http://127.0.0.1:8000/users/1001/items/foo?q=bar&short=false
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: Union[str, None] = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    print(f"short: {short}")
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item

@app.get("/set-cookie") 
def set_cookie(response: Response): 
    response.set_cookie(key="my_cookie", value="cookie_value") 
    return {"message": "Cookie set"}

# http://127.0.0.1:8000/items/foo?short=true
# http://127.0.0.1:8000/items/foo?q=bar&short=false
@app.get("/items/{item_id}")
async def read_item(
    item_id: str,
    q: Union[str, None] = None,
    short: bool = False):
    
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item

# ページング
# http://127.0.0.1:8000/items/?skip=0&limit=10
fake_items_db = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"}]

@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]



# http://127.0.0.1:8000/files/home/johndoe/myfile.txt
@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}

# http://127.0.0.1:8000/planets/earth
@app.get("/planets/{model_name}")
async def get_model(model_name: Planet = Planet.earth):
    
    if model_name is Planet.sun: 
        return {"model_name": model_name, "message": "Sun!"} 
    elif model_name is Planet.moon: 
        return {"model_name": model_name, "message": "Moon!"} 
    elif model_name is Planet.earth: 
        return {"model_name": model_name, "message": "Earth!"} 
    else: return {"model_name": model_name, "message": "No!"}




