# routers/router.py
from fastapi import APIRouter

sample_router = APIRouter(
    tags=["sample"]
)

# 呼び方
# https://127.0.0.1:8000/api/items
@sample_router.get("/items/", tags=["sample"])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

from fastapi.responses import JSONResponse
from config.config_loader import load_holiday_map


@sample_router.get("/check_holiday")
async def check_holiday(date: str):
    """
    指定された日付が祝日かどうかを判定し、祝日名を返すAPI
    例: /api/check_holiday?date=2025/1/1
    """
    holiday_map = load_holiday_map()
    holiday_name = holiday_map.get(date)

    return JSONResponse(content={"holiday_name": holiday_name or ""})
