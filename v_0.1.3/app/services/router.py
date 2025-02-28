# router.py
from fastapi import FastAPI
from fastapi import APIRouter

router = APIRouter()

# 呼び方
# https://127.0.0.1:8000/api/items
@router.get("/items/")
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
