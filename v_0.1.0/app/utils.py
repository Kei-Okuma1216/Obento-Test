# utils.py
from datetime import datetime, timezone, timedelta
from fastapi import Request, Response
from functools import wraps
import functools
import inspect
from typing import Dict
import warnings


# カスタムデコレーターを定義
# @log_decoratorを関数の上に記述すると、関数の前後にログを出力する
def log_decorator(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        print(f"- {func.__name__} 前")
        result = await func(*args, **kwargs)
        print(f"- {func.__name__} 後")
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        print(f"- {func.__name__} 前")
        result = func(*args, **kwargs)
        print(f"- {func.__name__} 後")
        return result

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# @deprecated
def deprecated(func):
    """This is a decorator to mark functions as deprecated."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__} is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return wrapper

# 日本標準時 (JST) のタイムゾーン定義
JST = timezone(timedelta(hours=9))

def get_now(tz : timezone = None) -> datetime:
    current_datetime = None
    if tz == JST:
        current_datetime = datetime.now(JST)
    else:
        current_datetime = datetime.now()
    #print(f"get_now(): {current_datetime}")
    return current_datetime
    
def get_date_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

def get_datetime_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")
    
# 今日の日付取得 update_datetime用
#@log_decorator
def get_today_str(offset: int = 0, date_format: str = None):
    new_date = get_now() + timedelta(days=offset)
    if date_format == "YMD":
        ymd = new_date.strftime("%Y-%m-%d")
    else:
        ymd = new_date.strftime("%Y-%m-%d %H:%M")
    #print(f"get_today_str(): {ymd}")
    return ymd

@log_decorator
def set_all_cookies(response: Response, data: Dict[str, str]):
    try:
        # これを試してみる↓
        #future_time = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        
        username = data['sub']
        token = data['token']
        exp = data['max-age']
        permission = data['permission']
        
        response.set_cookie(key="token", value=token, expires=exp)
        #response.set_cookie(key="exp", value=exp, expires=exp)
        response.set_cookie(key="sub", value=username, expires=exp)
        response.set_cookie(key="permission", value=permission, expires=exp)
        
        print("set all cookies")
        print(f" UserName: {username}")
        print(f" Token: {token}")
        print(f" Max-Age: {exp}")
        print(f" Permission: {permission}")
        
    except KeyError as e:
        print(f"Missing key: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

@log_decorator
def get_all_cookies(request: Request) -> Dict[str, str]:
    try:
        username = request.cookies.get("sub")
        print(f"cookies['sub']: {username}")
        
        if username is None:
            print("")
            #print("cookies['sub']が存在しません")
            #return HTMLResponse("<html><p>ユーザー情報が取得できませんでした。</p></html>")
        else:      
            print("")  
            
        
        
        token = request.cookies.get("token")
        #exp = request.cookies.get("exp")
        permission = request.cookies.get("permission")
        data = {
            "sub": username,
            "token": token,
            #"exp": int(exp),
            "permission": int(permission),
        }
        return data
    except KeyError as e:
        print(f"Missing key: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

@log_decorator
def delete_all_cookies(response: Response):
    try:
        response.delete_cookie(key="sub")
        response.delete_cookie(key="token")
        #response.delete_cookie(key="exp")
        response.delete_cookie(key="permission")
        response.delete_cookie(key="last_order_date")
        print("all cookies deleted")
    except KeyError as e:
        print(f"Missing key: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

@log_decorator
def compare_expire_date(exp_unix_str: str) -> bool:
    # UTCからUNIX値変換
    print(f"exp_unix_str :{exp_unix_str}")    
    exp_unix_int = int(exp_unix_str)
    
    now_utc_int = int(datetime.now(timezone.utc).timestamp()) 
    print(f"now_utc_int: {now_utc_int}")
    # 有効期限をチェック
    print(f"now: {now_utc_int} < exp: {exp_unix_int}")
    if now_utc_int < exp_unix_int:
        print("有効期限が無効です")  # 期限切れ
        return False
    else:
        print("有効期限は有効です")  # まだ有効
    return True

# 二重注文の禁止
# 設定
@log_decorator
def prevent_order_twice(response: Response, last_order_date: datetime):
    end_of_day = get_end_of_today() 
    print(f"end_of_day: {end_of_day}")
    end_time = get_max_age(end_of_day)
    print(f"max_time: {end_time}")
    current = datetime.now(JST)
    print(f"now: {current}")
    current_time = get_max_age(current)
    print(f"current_time: {end_time}")
    future_time = end_time - current_time
    print(f"future_time: {end_time}")
    
    response.set_cookie(
        key="last_order_date", value=last_order_date, max_age=future_time)
    print("# 期限を本日の23:59:59にした")

# 期限として本日の23:59:59を作成
@log_decorator
def get_end_of_today() -> datetime:
    today = datetime.now(JST)  # JSTで現在時刻を取得
    end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
    print(f"JST end_of_day: {end_of_day}")
    return end_of_day

# UNIX時間に変換
@deprecated
def get_max_age(dt: datetime) -> int:
    unix_time = int(dt.timestamp())
    #print(f"unix_time: {unix_time}")
    return unix_time

# チェックする
#@log_decorator
def stop_twice_order(request: Request):
    last_order = request.cookies.get("last_order_date")
    print(f"last_order: {last_order}")
    if last_order != None: # 注文処理をやめる
        return True
    else:
        return False

# max-ageを取り出す関数
def getout_max_age(set_cookie_header):
    # ヘッダーを分割して各属性に分ける
    parts = set_cookie_header.split(";")
    for part in parts:
        # 各属性をトリムして"max-age"が含まれているか確認
        part = part.strip()
        if part.lower().startswith("max-age"):
            # max-ageの値を取り出して返す
            return part.split("=")[1]
    # max-ageが見つからなかった場合
    return None

def convert_to_max_age(max_age : int):
    days = max_age / (60*60*24)
    nokori =  days * (60*60*24)
    nokori = nokori % (60*60)
    hours = nokori / 60*60
    