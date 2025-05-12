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

# @sample_router.get("/delivery/{order_day}")
# def get_delivery_day(order_day: int):
#     return {"order_day": order_day, "delivery_day":
#     delivery_mapping.get(order_day, "Invalid order day")}
from datetime import datetime, timedelta
from utils.utils import log_decorator

@log_decorator
def get_non_holiday_date(start_date: datetime) -> datetime:
    """
    祝日を飛ばして次の平日を取得する
    """
    holiday_map = load_holiday_map()

    while True:
        date_str = start_date.strftime("%Y/%-m/%-d")  # 例: 2025/1/1
        if holiday_map.get(date_str) is None:
            return start_date
        start_date += timedelta(days=1)

@sample_router.get("/delivery_date/{date_str}")
@log_decorator
def get_delivery_date(date_str: str):
    """
    指定された日付（YYYY-MM-DD）から配達可能日を判定するAPI
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    # 祝日をスキップ
    valid_date = get_non_holiday_date(date)

    # 曜日判定
    weekday = valid_date.weekday()  # 0: 月曜日 ～ 6: 日曜日
    delivery_day = delivery_mapping.get(weekday, "Invalid weekday")

    return {
        "order_date": valid_date.strftime("%Y-%m-%d"),
        "weekday": weekday,
        "delivery_day": delivery_day
    }

