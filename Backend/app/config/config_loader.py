# config/config_loader.py
import json
import os

def load_permission_map(path: str = "config/redirect_main_by_permission_map.json") -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Permissionマップファイルが見つかりません: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# def load_holiday_map(path: str = "config/holidays_map.json") -> dict:
#     ''' 祝日マップを読み込む関数
#     祝日マップは、祝日をキーにして、祝日の日付を値とする辞書型のデータ構造です。
#     holiday_name = holiday_map[str(date)]'''
#     if not os.path.exists(path):
#         raise FileNotFoundError(f"Permissionマップファイルが見つかりません: {path}")

#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)

# キャッシュ用変数（モジュールスコープ）
_cached_holiday_map = None

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
