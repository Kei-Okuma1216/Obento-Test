# config/config_loader.py
import json
import os
from utils.decorator import log_decorator

# 権限別main画面遷移マップを読み込む関数
@log_decorator
def load_permission_map(path: str = "config/redirect_main_by_permission_map.json") -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Permissionマップファイルが見つかりません: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

'''------------------------------------------------------------'''
# キャッシュ用変数（モジュールスコープ）
_cached_holiday_map = None
# @log_decorator
def load_holiday_map(path: str = "config/holidays_map.json") -> dict:
    ''' 祝日マップを読み込む関数（キャッシュ対応）'''
    # holiday_map = load_holiday_map()
    # holiday_name = holiday_map.get("2025/1/1")
    # print(holiday_name)  # "元日"
    global _cached_holiday_map

    if _cached_holiday_map is not None:
        # キャッシュが存在すればそれを返却
        return _cached_holiday_map

    if not os.path.exists(path):
        raise FileNotFoundError(f"祝日マップファイルが見つかりません: {path}")

    with open(path, "r", encoding="utf-8") as f:
        _cached_holiday_map = json.load(f)

    return _cached_holiday_map


from log_unified import logger
from pprint import pprint
from datetime import datetime, timedelta

# 配達可能曜日決定辞書
delivery_mapping = {
    0: 1,  # 月 -> 火
    1: 2,  # 火 -> 水
    2: 4,  # 水 -> 金
    3: 4,  # 木 -> 金
    4: 5,  # 金 -> 土
    5: 0,  # 土 -> 月
    6: 0   # 日 -> 月
}

# @log_decorator
async def skip_holiday(start_date: datetime) -> datetime:
    # print(f"初回 start_date: {start_date}")
    init_date = start_date.strftime('%Y-%m-%d')
    # print(f"注文日: {init_date}")
    
    holiday_map = load_holiday_map()

    while True:
        # 現在の日付の曜日を取得
        weekday = start_date.weekday()  # 0: 月 ~ 6: 日
        target_weekday = delivery_mapping.get(weekday)

        # 曜日が一致するまで日付を進める
        while start_date.weekday() != target_weekday:
            start_date += timedelta(days=1)

        # 日付文字列を "YYYY/M/D" 形式に変換
        date_str = f"{start_date.year}/{start_date.month}/{start_date.day}"
        # print(f"判定対象の日付: {date_str}")

        # 祝日でなければ採用
        if holiday_map.get(date_str) is None:
            # print(f"非祝日として確定: {start_date}")
            logger.debug(f"skip_holiday() 注文日: {init_date} 配達予定日: {start_date.strftime('%Y-%m-%d')}")

            return start_date.date()

        # 祝日なら翌日に進めて再判定
        start_date += timedelta(days=1)
