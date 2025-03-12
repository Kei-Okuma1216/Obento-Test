# utils.py
from datetime import datetime, timezone, timedelta
from dateutil import parser

from http.cookies import SimpleCookie
from venv import logger
from fastapi import Request, Response
from functools import wraps
from typing import Dict, Optional
from utils.exception import CustomException, CookieException

import functools
import inspect
import warnings

# カスタムデコレーターを定義
# @log_decoratorを関数の上に記述すると、関数の前後にログを出力する
def log_decorator(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        print(f"- {func.__name__} 前")
        logger.debug(f"- {func.__name__} 前")
        result = await func(*args, **kwargs)
        print(f"- {func.__name__} 後")
        logger.debug(f"- {func.__name__} 後")
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        print(f"- {func.__name__} 前")
        logger.debug(f"- {func.__name__} 前")
        result = func(*args, **kwargs)
        print(f"- {func.__name__} 後")
        logger.debug(f"- {func.__name__} 後")
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

#@log_decorator
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
@log_decorator
def get_today_str(offset: int = 0, date_format: str = None):
    new_date = get_now(JST) + timedelta(days=offset)
    if date_format == "YMD":
        ymd = new_date.strftime("%Y-%m-%d")
    else:
        ymd = new_date.strftime("%Y-%m-%d %H:%M")
    #print(f"get_today_str(): {ymd}")
    return ymd

@log_decorator
def set_all_cookies(response: Response, user: Dict):
    try:
        username = user['sub']
        token = user['token']
        permission = user['permission']
        max_age = user['max-age']

        # expiresを30日後に設定する
        future_time = datetime.now(timezone.utc) + timedelta(days=30)
        new_expires = future_time.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

        '''print("set all cookies")
        print(f" UserName: {username}")
        print(f" Token: {token}")
        print(f" max-age: {max_age}")
        print(f" Permission: {permission}")'''

        response.set_cookie(key="token", value=token, expires=new_expires)
        response.set_cookie(key="sub", value=username, expires=new_expires)
        response.set_cookie(key="permission", value=permission, expires=new_expires)

        logger.debug(f"set_all_cookies() - sub: {username}")
        logger.debug(f"set_all_cookies() - token: {token}")
        #logger.debug(f"set_all_cookies() - new_expires: {new_expires}")
        logger.debug(f"set_all_cookies() - permission: {permission}")

        return new_expires
        
    except KeyError as e:
        print(f"Missing key: {e}")
    except Exception as e:
        raise CookieException(
            method_name="set_all_cookies()",
            message=str(e))

#@log_decorator
def get_all_cookies(request: Request) -> Optional[Dict[str, str]]:
    try:
        username = request.cookies.get("sub")
        print(f"cookies['sub']: {username}")

        if username is None:
            logger.info("set_all_cookies() - cookies['sub']が存在しません")
            #print("cookies['sub']が存在しません")
            #return HTMLResponse("<html><p>ユーザー情報が取得できませんでした。</p></html>")
            return None

        token = request.cookies.get("token")
        #exp = request.cookies.get("exp")
        permission = request.cookies.get("permission")

        # いずれかが None の場合は例外を発生
        ''' 実装しない。理由：初回アクセスはCookieがないから
            if None in (username, token, exp, permission):
            raise CookieException(
                method_name="get_all_cookies",
                detail="必須のクッキーが不足しています")'''

        # permission は整数に変換
        #permission = int(permission)

        set_cookie_header = request.headers.get("cookie")
        # `Set-Cookie` をパース
        cookie = SimpleCookie()
        cookie.load(set_cookie_header)

        # `max-age` を取得
        max_age = cookie["token"]["max-age"] if "token" in cookie and "max-age" in cookie["token"] else None

        '''logger.debug(f"get_all_cookies() - sub: {username}")
        logger.debug(f"get_all_cookies() - token: {token}")
        logger.debug(f"get_all_cookies() - exp: {exp}")
        logger.debug(f"get_all_cookies() - permission: {permission}")
        logger.debug(f"get_all_cookies() - max-age: {max_age}")'''

        data = {
            "sub": username,
            "token": token,
            "max-age": max_age,
            "permission": int(permission)
        }

        return data

    except KeyError as e:
        print(f"Missing key: {e}")
    except ValueError:
        raise CookieException(
            method_name="get_all_cookies",
            detail="値が不正です")
    except Exception as e:
        raise

@log_decorator
def delete_all_cookies(response: Response):
    try:
        response.delete_cookie(key="sub")
        response.delete_cookie(key="token")
        response.delete_cookie(key="max-age")
        response.delete_cookie(key="permission")
        response.delete_cookie(key="last_order_date")
        logger.debug("delete_all_cookies()", "all cookies deleted")

    except KeyError as e:
        print(f"Missing key: {e}")
    except Exception as e:
        raise CookieException(
            method_name="delete_all_cookies()",
            message=str(e))

@log_decorator
#def compare_expire_date(exp_unix_str: str) -> bool:
def compare_expire_date(max_age: int) -> bool:
    # UTCからUNIX値変換
    #logger.debug(f"exp_unix_str :{exp_unix_str}")
    #exp_unix_int = int(exp_unix_str)
    
    #max_age = convert_expires_to_max_age(exp_unix_str)

    #now_utc_int = int(datetime.now(timezone.utc).timestamp())
    now_utc_datetime = get_now(JST) 
    now_utc_int = int(now_utc_datetime.timestamp()) 

    # 有効期限をチェック
    logger.debug(f"現在: {now_utc_int} < max_age: {max_age}")
    if  now_utc_int > max_age:
    #if  now_utc_int < max_age:
        logger.info("有効期限が無効です")  # 期限切れ
        return True

    logger.debug("有効期限は有効です")  # まだ有効
    return False

# 二重注文の禁止
# 設定
@log_decorator
def prevent_order_twice(response: Response, last_order_date: datetime):
    end_of_day = get_end_of_today() 
    end_time = convert_max_age(end_of_day)
    current = datetime.now(JST)
    current_time = convert_max_age(current)
    future_time = end_time - current_time

    logger.debug(f"end_of_day: {end_of_day}")
    logger.debug(f"max_time: {end_time}")
    logger.debug(f"now: {current}")
    logger.debug(f"current_time: {end_time}")
    logger.debug(f"future_time: {end_time}")

    response.set_cookie(
        key="last_order_date", value=last_order_date,
        max_age=future_time, httponly=True)
    logger.debug("# 期限を本日の23:59:59にした")

# 期限として本日の23:59:59を作成
#@log_decorator
def get_end_of_today() -> datetime:
    today = datetime.now(JST)  # JSTで現在時刻を取得
    end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
    logger.debug(f"JST end_of_day: {end_of_day}")

    return end_of_day

# UNIX時間に変換
@log_decorator
def convert_max_age(dt: datetime) -> int:
    unix_time = int(dt.timestamp())
    
    logger.debug(f"unix_time: {unix_time}")
    return unix_time

@log_decorator
def get_max_age(request: Request) -> int:
    try:
        set_cookie_header = request.headers.get("cookie")
        # `Set-Cookie` をパース
        cookie = SimpleCookie()
        cookie.load(set_cookie_header)

        # `max-age` を取得
        max_age = cookie["token"]["max-age"] if "token" in cookie and "max-age" in cookie["token"] else None

        max_age_int = int(max_age)
        #return {"max_age": max_age}

        logger.debug(f"max_age: {max_age_int}")

        return max_age_int

    except Exception:
        raise CookieException("get_max_age()")


# チェックする
@log_decorator
def stop_twice_order(request: Request):
    last_order = request.cookies.get("last_order_date")
    print(f"last_order: {last_order}")
    if last_order != None:
        return True # 注文処理をやめる
    else:
        return False

# max-ageを取り出す関数
def get_exp_value(set_cookie_header):
    # ヘッダーを分割して各属性に分ける
    parts = set_cookie_header.split(";")
    for part in parts:
        # 各属性をトリムして"max-age"が含まれているか確認
        part = part.strip()
        if part.lower().startswith("exp"):
            # max-ageの値を取り出して返す
            return part.split("=")[1]
    # max-ageが見つからなかった場合
    return None

'''max-age変換
 例えば、3600秒 (1時間)
 max_age = 3600
 days, hours, minutes, seconds = convert_max_age_to_dhms(max_age)
 print(f"{days}日 {hours}時間 {minutes}分 {seconds}秒")
'''
# max_ageを指定日時に変換する
def convert_max_age_to_dhms(max_age : int, add_date: datetime = None):    
    if add_date:
        add_max_age = convert_dhms_to_max_age(add_date.day, add_date.hour, add_date.minute, add_date.second)
        max_age = max_age + add_max_age
    days = max_age // 86400
    hours = (max_age % 86400) // 3600
    minutes = (max_age % 3600) // 60
    seconds = max_age % 60

    return days, hours, minutes, seconds

# 指定日時をmax_ageに変換する
def convert_dhms_to_max_age(days: int, hours: int, minutes: int, seconds: int) -> int:
    max_age = days * 86400 + hours * 3600 + minutes * 60 + seconds

    return max_age

# expires（UTC値の年月日時刻）をmax_age（秒）に変換する
def convert_expires_to_max_age(expires: str) -> int:
    try:
        # expiresをdatetimeオブジェクトに変換
        #expires_datetime = datetime.fromisoformat(expires).replace(tzinfo=timezone.utc)

        # expiresをdatetimeオブジェクトに変換
        expires_datetime = parser.isoparse(expires).replace(tzinfo=timezone.utc)


        # 現在のUTC時刻を取得
        #current_utc_time = get_now() #datetime.now(timezone.utc)

        # expiresまでの差を計算
        delta = expires_datetime - get_now()#current_utc_time
        
        # 差を秒に変換
        max_age = int(delta.total_seconds())

        return max_age

    except Exception:
        raise CustomException(
            500,
            "max_age変換に失敗しました。"
        )


from datetime import datetime, timedelta, timezone

'''
# 使用例
get_now = datetime.now  # デモ用のget_now関数
expired_time = get_now() + timedelta(days=30)
expires = convert_expired_time_to_expires(expired_time)
print(expires)
'''
def convert_expired_time_to_expires(expired_time: datetime) -> str:
    # expired_timeをUTCに変換
    expired_time_utc = expired_time.astimezone(timezone.utc)
    
    # ISO形式の文字列に変換
    expires = expired_time_utc.isoformat().replace('+00:00', 'Z')
    
    return expires
'''
# 権限チェック
@deprecated
@log_decorator
def check_permission(request: Request, allowed_permissions: Optional[List[int]] = None):
    permission = request.cookies.get("permission")
    logger.debug(f"check_permission(): {permission}")
    if permission is None:
        #allowed_permissions = [99]
        raise HTTPException(status_code=403, detail="Permission Data is not Contained")
    if permission == 99:
        logger.debug(f"permission: {permission}")
    elif permission in allowed_permissions:
        logger.debug(f"permission: {permission}")
    else:
        raise HTTPException(status_code=403, detail="Not Authorized")
'''
