from typing import Set, Union

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
# 
# https://fastapi.tiangolo.com/ja/tutorial/path-operation-configuration/#docstring

class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None
    tags: Set[str] = set()


@app.post("/items/", response_model=Item, summary="Create an item",
response_description="The created item"
          )
async def create_item(item: Item):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    return item