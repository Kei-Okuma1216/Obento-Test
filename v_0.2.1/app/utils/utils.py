# utils/utils.py
'''
    1. def log_decorator(func):
    2. def deprecated(func):

    3. JST
    4. def get_now(tz : timezone = None) -> datetime:
    5. def get_today_str(offset: int = 0, date_format: str = None):
        JSTの("%Y-%m-%d %H:%M:%S")を返す
    6. async def get_created_at_period(days_ago: int) -> Tuple[datetime, datetime]:
    7. def get_today_datetime(days_ago: int = 0)-> datetime:

    11. def set_all_cookies(response: Response, user: Dict):
    12. def get_all_cookies(request: Request) -> Optional[Dict[str, str]]:
    13. def delete_all_cookies(response: Response):
    14. def compare_expire_date(expires: str) -> bool:
    15. def prevent_order_twice(response: Response, last_order_date: datetime):
    16. def get_end_of_today(tz : timezone = None) -> datetime:
    17. def get_token_expires(request: Request) -> str:

    18. async def check_permission_and_stop_order(request: Request, response: Response):
    19. async def check_permission(request: Request, permits: list):

'''
    
from datetime import datetime, timezone, timedelta

from venv import logger
from fastapi import Request, Response
from http.cookies import SimpleCookie

from functools import wraps
from typing import Dict, Optional

import functools
import inspect
import warnings


from utils.exception import CookieException, CustomException

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
    # utcnow()は禁止
    current_datetime = None
    if tz == JST:
        current_datetime = datetime.now(JST)
    else:
        current_datetime = datetime.now()
    return current_datetime


# 今日の日付取得 update_datetime用
#@log_decorator
def get_today_str(offset: int = 0, date_format: str = None):
    # new_date = get_now(JST) + timedelta(days=offset)
    new_date = get_today_datetime() + timedelta(days=offset)
    
    get_today_datetime
    if date_format == "YMD":
        ymd = new_date.strftime("%Y-%m-%d")
    else:
        ymd = new_date.strftime("%Y-%m-%d %H:%M:%S")

    print(f"get_today_str(): {ymd}")
    return ymd



import pytz

from datetime import datetime, timedelta
from typing import NamedTuple

class Period(NamedTuple):
    # 返却値が入れ替わるので、専用のクラスを作った
    start: datetime
    end: datetime

@log_decorator
async def get_created_at_period(days_ago: int) -> Period: #Tuple[datetime, datetime]:
    """
    指定された days_ago に基づいて、期間の開始日時と終了日時を返す。
    返す datetime は tzinfo を持たない naive datetime。
    開始: 00:00:00、終了: 23:59:59
    """
    try:
        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        
        start_target = now - timedelta(days=days_ago)
        end_target = now  # 今日の終端とするため、nowの日付だけ使う

        start_dt = datetime(start_target.year, start_target.month, start_target.day, 0, 0, 0)
        end_dt   = datetime(end_target.year, end_target.month, end_target.day, 23, 59, 59)

        print(f"{start_dt=}, {end_dt=}")

        return Period(start_dt, end_dt)

    except Exception as e:    
        raise CustomException(500, "get_created_at_period()", f"Error: {e}")


@log_decorator
def get_today_datetime(days_ago: int = 0) -> datetime:
    """
    JSTで days_ago 日前の0時0分0秒のナイーブな datetime を返す。
    例: days_ago=0 -> 今日の 00:00:00（タイムゾーンなし）
    """
    tz = pytz.timezone("Asia/Tokyo")
    current_time = datetime.now(tz) - timedelta(days=days_ago)

    # JST基準で「0時0分0秒」の日時を作成（tzなしで返す）
    naive_datetime = datetime(
        current_time.year,
        current_time.month,
        current_time.day,
        current_time.hour,
        current_time.minute,
        current_time.second,
        0
        # 0, 0, 0, 0
    )

    print(f"{naive_datetime=}, {naive_datetime.tzinfo=}")
    return naive_datetime


def get_naive_jst_now() -> datetime:
    """Asia/Tokyo の現在時刻を tzinfo なしで返す
    日付取得はasyncにする必要なし
    """
    return datetime.strptime(
        datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S"),
        "%Y-%m-%d %H:%M:%S"
    )


@log_decorator
def set_all_cookies(response: Response, user: Dict):
    try:
        username = user['sub']
        token = user['token']
        permission = user['permission']

        # expiresを30日後に設定する
        future_time = datetime.now(timezone.utc) + timedelta(days=30)
        new_expires = future_time.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

        response.set_cookie(key="token", value=token, expires=new_expires)
        response.set_cookie(key="sub", value=username, expires=new_expires)
        response.set_cookie(key="permission", value=permission, expires=new_expires)

        logger.debug(f"sub: {username}, permission: {permission}, token: {token}, expires: {new_expires}")
        return new_expires
        
    except KeyError as e:
        logger.error(f"Missing key: {e}")
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
            logger.info("get_all_cookies() - 初回アクセスは cookies['sub']が存在しません")
            return None

        token = request.cookies.get("token")
        permission = request.cookies.get("permission")

        # `Set-Cookie` をパース
        set_cookie_header = request.headers.get("cookie")
        cookie = SimpleCookie()
        cookie.load(set_cookie_header)

        # `max-age` を取得
        expires = cookie["token"]["expires"] if "token" in cookie and "expires" in cookie["token"] else None

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
        response.delete_cookie(key="permission")
        #response.delete_cookie(key="order_twice")
        response.delete_cookie(key="last_order_date")

        logger.debug("delete_all_cookies()", "all cookies deleted")

    except KeyError as e:
        print(f"Missing key: {e}")
    except Exception as e:
        raise CookieException(
            method_name ="delete_all_cookies()",
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
        # 初回アクセスなど、expires が空の場合は有効期限チェックをスキップする
        if not expires:
            logger.debug("expires が存在しないため、有効期限のチェックをスキップします")
            return False

        # `expires` を datetime に変換
        expire_datetime = datetime.fromisoformat(expires.replace('Z', '+00:00')).astimezone(timezone.utc)

        # 現在の UTC 時刻
        now_utc_datetime = datetime.now()#get_now()
        now_utc_int = int(now_utc_datetime.timestamp())
        expire_int = int(expire_datetime.timestamp())

        # 有効期限をチェック
        logger.debug(f"現在: {now_utc_int} < expires: {expire_int}")

        if now_utc_int > expire_int:
            logger.info("有効期限が無効です")  # 期限切れ
            return True

        logger.debug("有効期限は有効です")  # まだ有効
        return False

    except CookieException as e:
        raise
    except Exception as e:
        raise 


# 二重注文の禁止
# 設定
@log_decorator
def prevent_order_twice(response: Response, last_order_date: datetime):

    end_of_day = get_end_of_today(JST)
    end_time = int(end_of_day.timestamp())

    current = get_today_datetime()#get_now(JST)
    current_time = int(current.timestamp())

    future_time = end_time - current_time

    logger.debug(f"last_order_date: {last_order_date}")
    logger.debug(f"future_time: {future_time}")

    response.set_cookie(
        key="last_order_date", value=last_order_date,
        max_age=future_time, httponly=True)
    logger.debug("# 期限を本日の23:59:59にした")

# 期限として本日の23:59:59を作成
#@log_decorator
def get_end_of_today(tz : timezone = None) -> datetime:
    today = None
    if tz == JST:
        today = datetime.now(JST)
    else:
        today = datetime.now()

    end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
    logger.debug(f"JST end_of_day: {end_of_day}")

    return end_of_day


@log_decorator
def get_token_expires(request: Request) -> str:
    try:
        set_cookie_header = request.headers.get("cookie")
        # Cookie ヘッダーが存在しない場合は初回アクセスとみなし、None を返す
        if not set_cookie_header:
            logger.debug("Cookie header が存在しないため、expires の取得をスキップします")
            return None

        cookie = SimpleCookie()
        cookie.load(set_cookie_header)

        if cookie["token"]["expires"] is None:
            print("token expires なし")
            return None

        expires = cookie["token"]["expires"] if "token" in cookie and "expires" in cookie["token"] else None

        logger.debug(f"expires: {expires}")

        return expires

    except Exception as e:
        raise CookieException(
            method_name="get_token_expires()",
            detail="expiresが正常に取得できませんでした。",
            exception=e
        )


# チェックする
#@log_decorator
async def check_permission_and_stop_order(request: Request, response: Response):
    try:
        ''' 権限と二重注文チェックを合体させた関数
            - cookie permissionが1の場合に限り実行する。
            - last_order_dateが存在していればTrueを返す
            - それ以外の場合はFalseを返す
        '''
        # Cookieからpermissionを取得
        permission = request.cookies.get("permission")
        #print(f"cookie permission: {permission}")

        if permission is None:
            permission = '1'

        if permission != '' and permission.isdigit():
            permission = int(permission)
        #print(f"permission: {permission}")

        # permissionが1である場合のみ、二重注文（last_order_date）のチェックを行う
        if permission == 1:
            last_order = request.cookies.get("last_order_date")
            if last_order is None:
                return False, None
            else:
                logger.info(f"check_permission_and_stop_order() - きょう２度目の注文を阻止 - 最終注文日: {last_order}")
                logger.debug(f"result , last_order: {True , str(last_order)}")
                return True, last_order
        else:
            # Cookieを全部消す
            delete_all_cookies(response)
            return False, None

    except (KeyError, Exception) as e:
        raise CookieException(
            method_name="check_permission_and_stop_order()",
            detail="last_order_dateが正常に取得できませんでした。",
            exception=e
        )

@log_decorator
async def check_permission(request: Request, permits: list):
    ''' 権限チェック '''
    permission = request.cookies.get("permission")

    # print(f"permission: {permission}")
    if permission is None or permission == '':
        permission = 0

    if isinstance(permission, str) and permission.isdigit():
        permission = int(permission)

    # print(f"permits: {permits}")
    if permission in permits:
        return True

    return False
