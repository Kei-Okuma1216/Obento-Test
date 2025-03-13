# router.py
from fastapi import APIRouter

sample_router = APIRouter(
    prefix="/sample",
    tags=["sample"]
)

# 呼び方
# https://127.0.0.1:8000/api/items
@sample_router.get("/items/", tags=["sample"])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
