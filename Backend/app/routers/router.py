# routers/router.py
'''

------------------------------------------------------------'''
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


# 配達可能曜日決定辞書
delivery_mapping = {
    0: 1, # 月 -> 火
    1: 2, # 火 -> 水
    2: 4, # 水 -> 金
    3: 4, # 木 -> 金
    4: 5, # 金 -> 土
    5: 0, # 土 -> 月
    6: 0 # 日 -> 月
}


from datetime import datetime
from utils.utils import log_decorator
from config.config_loader import skip_holiday


@sample_router.get("/delivery_date/{date_str}")
@log_decorator
async def delivery_date_view(date_str: str):
    """
    指定された日付（YYYY-MM-DD）から配達可能日を判定するAPI
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    # 祝日をスキップ
    valid_date = await skip_holiday(date)
    print(f"{valid_date}")

    # 曜日判定
    weekday = valid_date.weekday()  # 0: 月曜日 ～ 6: 日曜日
    delivery_day = delivery_mapping.get(weekday, "Invalid weekday")

    return {
        "order_date": valid_date.strftime("%Y-%m-%d"),
        "weekday": weekday,
        "delivery_day": delivery_day
    }

