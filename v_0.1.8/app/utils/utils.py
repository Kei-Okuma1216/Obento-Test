# utils.py
from datetime import datetime, timezone, timedelta

from http.cookies import SimpleCookie
from venv import logger
from fastapi import Request, Response
from functools import wraps
from typing import Dict, Optional
from utils.exception import CookieException

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
        ymd = new_date.strftime("%Y-%m-%d %H:%M:%S")
    print(f"get_today_str(): {ymd}")
    return ymd

@log_decorator
def set_all_cookies(response: Response, user: Dict):
    try:
        username = user['sub']
        token = user['token']
        permission = user['permission']
        #max_age = user['max-age']

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
            logger.info("get_all_cookies() - cookies['sub']が存在しません")
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
        expires = cookie["token"]["expires"] if "token" in cookie and "expires" in cookie["token"] else None

        '''logger.debug(f"get_all_cookies() - sub: {username}")
        logger.debug(f"get_all_cookies() - token: {token}")
        logger.debug(f"get_all_cookies() - exp: {exp}")
        logger.debug(f"get_all_cookies() - permission: {permission}")
        logger.debug(f"get_all_cookies() - max-age: {max_age}")'''

        data = {
            "sub": username,
            "token": token,
            "expires": expires,
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
        print("ここまできた 2")
        #response.delete_cookie(key="max-age")
        response.delete_cookie(key="permission")
        print("ここまできた 3")
        
        response.delete_cookie(key="last_order_date")
        logger.debug("delete_all_cookies()", "all cookies deleted")

    except KeyError as e:
        print(f"Missing key: {e}")
    except Exception as e:
        raise CookieException(
            detail="クッキー削除中にエラーが発生しました。",
            exception=e  # `e` を追加
            )

@log_decorator
def compare_expire_date(expires: str) -> bool:
    """
    クッキーの有効期限 (`expires`) を現在の UTC 時刻と比較し、期限切れかどうかを判定する。
    
    :param expires: ISO 8601 形式の UTC 日時 (`YYYY-MM-DDTHH:MM:SSZ`)
    :return: 期限が切れていれば True（無効）、まだ有効なら False（有効）
    """
    try:
        if expires is None:
            return True

        # `expires` を datetime に変換
        expire_datetime = datetime.fromisoformat(expires.replace('Z', '+00:00')).astimezone(timezone.utc)

        # 現在の UTC 時刻
        now_utc_datetime = get_now()
        now_utc_int = int(now_utc_datetime.timestamp())
        expire_int = int(expire_datetime.timestamp())

        # 有効期限をチェック
        logger.debug(f"現在: {now_utc_int} < expires: {expire_int}")
        
        if now_utc_int > expire_int:
            logger.info("有効期限が無効です")  # 期限切れ
            return True

        logger.debug("有効期限は有効です")  # まだ有効
        return False
    
    except Exception as e:
        logger.error(f"compare_expire_date() でエラー発生: {str(e)}")
        return True  # エラー時は期限切れとみなす


# 二重注文の禁止
# 設定
@log_decorator
def prevent_order_twice(response: Response, last_order_date: datetime):

    end_of_day = get_end_of_today() 
    end_time = int(end_of_day.timestamp())
    #end_time = convert_max_age(end_of_day)
    current = datetime.now(JST)
    #current_time = convert_max_age(current)
    current_time = int(current.timestamp())
    future_time = end_time - current_time

    logger.debug(f"end_of_day: {end_of_day}")
    logger.debug(f"max_time: {end_time}")
    logger.debug(f"now: {current}")
    logger.debug(f"current_time: {current_time}")
    logger.debug(f"future_time: {future_time}")

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

'''
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
        print("ここまできた 3")
        print(set_cookie_header)
        cookie.load(set_cookie_header)
        print("ここまできた 4")

        #print(f" token: {cookie["token"]}")
        print(f" token, expires: {cookie["token"]["expires"]}")
        print("ここまできた 5")
        if cookie["token"]["expires"] is None:
            print("token expires なし")
            return None
        # `max-age` を取得
        exp = cookie["token"]["expires"] if "token" in cookie and "expires" in cookie["token"] else None

        #max_age_int = int(max_age)
        #return {"max_age": max_age}

        logger.debug(f"expires: {exp}")

        return exp

    except Exception as e:
        raise CookieException(
            method_name="get_max_age()",
            detail="max-age取得でエラーが発生しました。",
            exception=e
        )
'''
@log_decorator
def get_expires(request: Request) -> str:
    try:
        set_cookie_header = request.headers.get("cookie")
        # `Set-Cookie` をパース
        cookie = SimpleCookie()
        #print("ここまできた 3")
        #print(set_cookie_header)
        cookie.load(set_cookie_header)
        #print("ここまできた 4")

        #print(f" token: {cookie["token"]}")
        #print(f" token, expires: {cookie["token"]["expires"]}")
        #print("ここまできた 5")
        if cookie["token"]["expires"] is None:
            print("token expires なし")
            return None

        # `expires` を取得
        expires = cookie["token"]["expires"] if "token" in cookie and "expires" in cookie["token"] else None

        logger.debug(f"expires: {expires}")

        return expires

    except Exception as e:
        raise CookieException(
            method_name="get_expires()",
            detail="expires取得でエラーが発生しました。",
            exception=e
        )


# チェックする
@log_decorator
def stop_twice_order(request: Request):
    last_order = request.cookies.get("last_order_date")
    print(f"last_order: {last_order}")
    if last_order != None:
        return True # 注文処理をやめる
    else:
        return False
'''
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
'''
'''max-age変換
 例えば、3600秒 (1時間)
 max_age = 3600
 days, hours, minutes, seconds = convert_max_age_to_dhms(max_age)
 print(f"{days}日 {hours}時間 {minutes}分 {seconds}秒")
'''
'''
def convert_expired_time_to_expires(expired_time: datetime) -> str:
    # expired_timeをUTCに変換
    expired_time_utc = expired_time.astimezone(timezone.utc)
    
    # ISO形式の文字列に変換
    expires = expired_time_utc.isoformat().replace('+00:00', 'Z')
    
    return expires
'''
