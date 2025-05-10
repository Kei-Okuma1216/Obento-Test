# utils/utils.py
'''
    1. def log_decorator(func):
    2. def deprecated(func):

    3. def get_today_str(offset: int = 0, date_format: str = None):
        JSTの("%Y-%m-%d %H:%M:%S")を返す
    4. async def get_created_at_period(days_ago: int) -> Tuple[datetime, datetime]:
    5. def get_today_datetime(days_ago: int = 0)-> datetime:
    6. def get_naive_jst_now() -> datetime:

    7. def set_all_cookies(response: Response, user: Dict):
    8. def get_all_cookies(request: Request) -> Optional[Dict[str, str]]:
    9. def delete_all_cookies(response: Response):
    10. def compare_expire_date(expires: str) -> bool:
    11. def prevent_order_twice(response: Response, last_order_date: datetime):
    12. def get_end_of_today(tz : timezone = None) -> datetime:
    13. def get_token_expires(request: Request) -> str:

    14. async def check_permission_and_stop_order(request: Request, response: Response):
    15. async def check_permission(request: Request, permits: list):

'''
    
from datetime import datetime, timezone, timedelta

import functools
from venv import logger

from fastapi import Request, Response
from http.cookies import SimpleCookie

from functools import wraps
from typing import Dict, Optional

import inspect
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

# def log_decorator(func):
#     @wraps(func)
#     async def async_wrapper(*args, **kwargs):
#         print(f"- {func.__name__} 前")
#         logger.debug(f"- {func.__name__} 前")
#         result = await func(*args, **kwargs)
#         print(f"- {func.__name__} 後")
#         logger.debug(f"- {func.__name__} 後")
#         return result

#     @wraps(func)
#     def sync_wrapper(*args, **kwargs):
#         print(f"- {func.__name__} 前")
#         logger.debug(f"- {func.__name__} 前")
#         result = func(*args, **kwargs)
#         print(f"- {func.__name__} 後")
#         logger.debug(f"- {func.__name__} 後")
#         return result

#     if inspect.iscoroutinefunction(func):
#         return async_wrapper
#     else:
#         return sync_wrapper

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

# 今日の日付取得 update_datetime用
#@log_decorator
def get_today_str(offset: int = 0, date_format: str = None):
    new_date = get_today_datetime() + timedelta(days=offset)

    if date_format == "YMD":
        ymd = new_date.strftime("%Y-%m-%d")
    else:
        ymd = new_date.strftime("%Y-%m-%d %H:%M:%S")

    print(f"get_today_str(): {ymd}")
    return ymd



import pytz

from typing import NamedTuple

class Period(NamedTuple):
    # 返却値が入れ替わるので、専用のクラスを作った
    start: datetime
    end: datetime

# @log_decorator

from fastapi import HTTPException, status
from log_unified import logger


@log_decorator
async def get_created_at_period(days_ago: int) -> Period:
    """
    指定された days_ago に基づいて、期間の開始日時と終了日時を返す。
    返す datetime は tzinfo を持たない naive datetime。
    開始: 00:00:00、終了: 23:59:59
    """
    try:
        # 型と値の検証
        if not isinstance(days_ago, int) or days_ago < 0:
            logger.warning(f"get_created_at_period() - 無効な days_ago: {days_ago}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_ago は 0 以上の整数で指定してください"
            )

        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        start_target = now - timedelta(days=days_ago)
        end_target = now

        start_dt = datetime(start_target.year, start_target.month, start_target.day, 0, 0, 0)
        end_dt   = datetime(end_target.year, end_target.month, end_target.day, 23, 59, 59)

        logger.debug(f"get_created_at_period() - start: {start_dt}, end: {end_dt}")

        return Period(start_dt, end_dt)

    except HTTPException:
        raise  # 既に投げた HTTPException はそのまま再スロー

    except (ValueError, TypeError) as e:
            logger.exception("get_created_at_period() - 型または値のエラー")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="期間計算中に不正なパラメータが指定されました"
            )

    except Exception as e:
        logger.exception("get_created_at_period() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="期間計算中にサーバーエラーが発生しました"
        )

# async def get_created_at_period(days_ago: int) -> Period: #Tuple[datetime, datetime]:
#     """
#     指定された days_ago に基づいて、期間の開始日時と終了日時を返す。
#     返す datetime は tzinfo を持たない naive datetime。
#     開始: 00:00:00、終了: 23:59:59
#     """
#     try:
#         now = datetime.now(pytz.timezone("Asia/Tokyo"))
        
#         start_target = now - timedelta(days=days_ago)
#         end_target = now  # 今日の終端とするため、nowの日付だけ使う

#         start_dt = datetime(start_target.year, start_target.month, start_target.day, 0, 0, 0)
#         end_dt   = datetime(end_target.year, end_target.month, end_target.day, 23, 59, 59)

#         print(f"{start_dt=}, {end_dt=}")

#         return Period(start_dt, end_dt)

#     except Exception as e:    
#         logger.error(f"get_created_at_period() - Error: {e}")
#         # raise CustomException(500, "get_created_at_period()", f"Error: {e}")

@log_decorator
def get_today_datetime(days_ago: int = 0) -> datetime:
    """
    JSTで days_ago 日前の0時0分0秒のナイーブな datetime を返す。
    例: days_ago=0 -> 今日の 00:00:00（タイムゾーンなし）
    """
    try:
        # 型と値の検証
        if not isinstance(days_ago, int) or days_ago < 0:
            logger.warning(f"get_today_datetime() - 無効な days_ago: {days_ago}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_ago は 0 以上の整数で指定してください"
            )

        tz = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(tz) - timedelta(days=days_ago)

        naive_datetime = datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            0, 0, 0
        )

        logger.debug(f"get_today_datetime() - 生成日時: {naive_datetime}")
        return naive_datetime

    except HTTPException:
        raise  # 既に投げた HTTPException はそのまま返す

    except (ValueError, TypeError) as e:
        logger.exception("get_today_datetime() - 型または値のエラー")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日付計算中に不正なパラメータが指定されました"
        )
    except Exception as e:
        logger.exception("get_today_datetime() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="日付計算中にサーバーエラーが発生しました"
        )

# # @log_decorator
# def get_today_datetime(days_ago: int = 0) -> datetime:
#     """
#     JSTで days_ago 日前の0時0分0秒のナイーブな datetime を返す。
#     例: days_ago=0 -> 今日の 00:00:00（タイムゾーンなし）
#     """
#     tz = pytz.timezone("Asia/Tokyo")
#     current_time = datetime.now(tz) - timedelta(days=days_ago)

#     # JST基準で「0時0分0秒」の日時を作成（tzなしで返す）
#     naive_datetime = datetime(
#         current_time.year,
#         current_time.month,
#         current_time.day,
#         current_time.hour,
#         current_time.minute,
#         current_time.second,
#         0
#     )

#     # print(f"{naive_datetime=}, {naive_datetime.tzinfo=}")
#     return naive_datetime


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
        # 必須フィールドの検証
        username = user.get('sub')
        token = user.get('token')
        permission = user.get('permission')

        if not all([username, token, permission]):
            missing_fields = [key for key in ['sub', 'token', 'permission'] if not user.get(key)]
            logger.warning(f"set_all_cookies() - 不足フィールド: {missing_fields}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ユーザーデータに必要なフィールドが不足しています: {', '.join(missing_fields)}"
            )

        # 有効期限の設定
        future_time = datetime.now(timezone.utc) + timedelta(days=30)
        new_expires = future_time.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

        # セキュア属性付き Cookie 設定
        cookie_options = {
            "expires": new_expires,
            "secure": True,           # HTTPSのみ
            "httponly": True,         # JavaScriptアクセス禁止
            "samesite": "Lax"         # クロスサイトGET許可
        }

        response.set_cookie(key="token", value=token, **cookie_options)
        response.set_cookie(key="sub", value=username, **cookie_options)
        response.set_cookie(key="permission", value=str(permission), **cookie_options)

        logger.debug(f"set_all_cookies() - sub: {username}, permission: {permission}, token: {token}, expires: {new_expires}")
        return new_expires

    except HTTPException:
        raise  # 既に投げたHTTPExceptionはそのまま返す

    except (TypeError, ValueError) as e:
        logger.exception("set_all_cookies() - ユーザーデータの形式が不正です")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザーデータの形式が不正です"
        )

    except Exception as e:
        logger.exception("set_all_cookies() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cookie設定中にサーバーエラーが発生しました"
        )


# @log_decorator
# def set_all_cookies(response: Response, user: Dict):
#     try:
#         username = user['sub']
#         token = user['token']
#         permission = user['permission']

#         # expiresを30日後に設定する
#         future_time = datetime.now(timezone.utc) + timedelta(days=30)
#         new_expires = future_time.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

#         response.set_cookie(key="token", value=token, expires=new_expires)
#         response.set_cookie(key="sub", value=username, expires=new_expires)
#         response.set_cookie(key="permission", value=permission, expires=new_expires)

#         logger.debug(f"sub: {username}, permission: {permission}, token: {token}, expires: {new_expires}")
#         return new_expires
        
#     except KeyError as e:
#         logger.error(f"Missing key: {e}")
#     except Exception as e:
#         logger.error(f"set_all_cookies() - Error: {e}")
#         # raise CookieException(
#         #     method_name="set_all_cookies()",
#         #     message=str(e))

from http.cookies import SimpleCookie

def get_all_cookies(request: Request) -> Optional[Dict[str, str]]:
    try:
        username = request.cookies.get("sub")
        print(f"cookies['sub']: {username}")

        if username is None:
            logger.info("get_all_cookies() - 初回アクセスは cookies['sub']が存在しません")
            return None

        token = request.cookies.get("token")
        permission_str = request.cookies.get("permission")

        if permission_str is None:
            logger.warning("get_all_cookies() - permissionが存在しません")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cookieに permission が存在しません"
            )

        try:
            permission = int(permission_str)
        except ValueError as ve:
            logger.exception("get_all_cookies() - permission の型変換に失敗")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cookieの permission が不正な値です"
            )

        # `Set-Cookie` をパース
        set_cookie_header = request.headers.get("cookie", "")
        cookie = SimpleCookie()
        cookie.load(set_cookie_header)

        expires = cookie["token"]["expires"] if "token" in cookie and "expires" in cookie["token"] else None

        data = {
            "sub": username,
            "token": token,
            "expires": expires,
            "permission": permission
        }

        return data

    except HTTPException:
        raise  # 既に投げたものはそのまま返す

    except KeyError as e:
        logger.exception(f"get_all_cookies() - 必要なキーが存在しません: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cookieデータに必要なキーが存在しません: {e}"
        )

    except Exception as e:
        logger.exception(f"get_all_cookies() - 予期せぬ例外が発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cookie取得中にサーバーエラーが発生しました"
        )

# #@log_decorator
# def get_all_cookies(request: Request) -> Optional[Dict[str, str]]:
#     try:
#         username = request.cookies.get("sub")
#         print(f"cookies['sub']: {username}")

#         if username is None:
#             logger.info("get_all_cookies() - 初回アクセスは cookies['sub']が存在しません")
#             return None

#         token = request.cookies.get("token")
#         permission = request.cookies.get("permission")

#         # `Set-Cookie` をパース
#         set_cookie_header = request.headers.get("cookie")
#         cookie = SimpleCookie()
#         cookie.load(set_cookie_header)

#         # `max-age` を取得
#         expires = cookie["token"]["expires"] if "token" in cookie and "expires" in cookie["token"] else None

#         data = {
#             "sub": username,
#             "token": token,
#             "expires": expires,
#             "permission": int(permission)
#         }

#         return data

#     except KeyError as e:
#         logger.error(f"get_all_cookies() - Missing key: {e}")
#     except ValueError:
#         logger.error(f"get_all_cookies() - Error: {e}")
#         # raise CookieException(
#         #     method_name="get_all_cookies",
#         #     detail="値が不正です")
#     except Exception as e:
#         logger.error(f"get_all_cookies() - 予期せぬ例外が発生しました: {e}")
#         raise

@log_decorator
def delete_all_cookies(response: Response):
    try:
        response.delete_cookie(key="sub")
        response.delete_cookie(key="token")
        response.delete_cookie(key="permission")
        # response.delete_cookie(key="order_twice")
        response.delete_cookie(key="last_order_date")

        logger.info("delete_all_cookies() - すべてのCookieを削除しました")

    except Exception as e:
        logger.exception("delete_all_cookies() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cookie削除中にサーバーエラーが発生しました"
        )

from datetime import datetime, timezone
from fastapi import HTTPException, status
from log_unified import logger


@log_decorator
def compare_expire_date(expires: str) -> bool:
    """
    クッキーの有効期限 (`expires`) を現在の UTC 時刻と比較し、期限切れかどうかを判定する。

    :param expires: ISO 8601 形式の UTC 日時 (`YYYY-MM-DDTHH:MM:SSZ`)
    :return: 期限が切れていれば True（無効）、まだ有効なら False（有効）
    """
    try:
        # 初回アクセスなど、expires が空の場合はスキップ（有効）
        if not expires:
            logger.debug("compare_expire_date() - expires が存在しないため、有効期限チェックをスキップ")
            return False

        # ISO 8601 日付パース
        try:
            expire_datetime = datetime.fromisoformat(expires.replace('Z', '+00:00')).astimezone(timezone.utc)
        except ValueError:
            logger.exception("compare_expire_date() - 不正な日付形式")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expires は ISO 8601 形式（YYYY-MM-DDTHH:MM:SSZ）で指定してください"
            )

        # 現在の UTC 時刻
        now_utc_int = int(datetime.now(timezone.utc).timestamp())
        expire_int = int(expire_datetime.timestamp())

        logger.debug(f"compare_expire_date() - 現在: {now_utc_int} < expires: {expire_int}")

        if now_utc_int > expire_int:
            logger.info("compare_expire_date() - 有効期限が切れています")
            return True

        logger.debug("compare_expire_date() - 有効期限は有効です")
        return False

    except HTTPException:
        raise  # 既に投げた HTTPException はそのまま再スロー

    except Exception as e:
        logger.exception("compare_expire_date() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="有効期限チェック中にサーバーエラーが発生しました"
        )



# 二重注文の禁止
# 設定
@log_decorator
def prevent_order_twice(response: Response, last_order_date: datetime):

    # end_of_day = get_end_of_today(JST)
    today = get_today_datetime()
    end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
    end_time = int(end_of_day.timestamp())

    current = get_today_datetime()
    current_time = int(current.timestamp())

    future_time = end_time - current_time

    logger.debug(f"last_order_date: {last_order_date}")
    logger.debug(f"future_time: {future_time}")

    response.set_cookie(
        key="last_order_date", value=last_order_date,
        max_age=future_time, httponly=True)
    logger.debug("# 期限を本日の23:59:59にした")

@log_decorator
def get_token_expires(request: Request) -> str:
    try:
        # Cookieヘッダー取得
        set_cookie_header = request.headers.get("cookie")
        if not set_cookie_header:
            logger.debug("get_token_expires() - Cookie header が存在しないため、expires の取得をスキップ")
            return None

        # Cookieパース
        cookie = SimpleCookie()
        try:
            cookie.load(set_cookie_header)
        except Exception as parse_error:
            logger.exception("get_token_expires() - Cookieのパースに失敗しました")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cookieヘッダーのフォーマットが不正です"
            )

        # tokenとexpiresの存在確認
        if "token" not in cookie:
            logger.debug("get_token_expires() - token Cookie が存在しません")
            return None

        expires = cookie["token"]["expires"] if "expires" in cookie["token"] else None

        if not expires:
            logger.debug("get_token_expires() - token expires が存在しません")
            return None

        logger.debug(f"get_token_expires() - 取得した expires: {expires}")
        return expires

    except HTTPException:
        raise  # 既に投げたHTTPExceptionはそのまま返す

    except Exception as e:
        logger.exception("get_token_expires() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="expires取得中にサーバーエラーが発生しました"
        )

@log_decorator
async def check_permission_and_stop_order(request: Request, response: Response):
    try:
        # Cookieからpermissionを取得
        permission_str = request.cookies.get("permission")
        logger.debug(f"check_permission_and_stop_order() - 取得した permission: {permission_str}")

        if not permission_str:
            logger.info("check_permission_and_stop_order() - permission が存在しないため、デフォルト '1' を設定")
            permission = 1
        else:
            if not permission_str.isdigit():
                logger.warning(f"check_permission_and_stop_order() - permission が不正: {permission_str}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cookieのpermissionが不正です"
                )
            permission = int(permission_str)

        # permissionが1である場合のみ、二重注文（last_order_date）チェック
        if permission == 1:
            last_order = request.cookies.get("last_order_date")
            if last_order is None:
                logger.debug("check_permission_and_stop_order() - 最終注文日が存在しない")
                return False, None
            else:
                logger.info(f"check_permission_and_stop_order() - 今日２度目の注文を阻止 - 最終注文日: {last_order}")
                return True, last_order
        else:
            try:
                delete_all_cookies(response)
                logger.info("check_permission_and_stop_order() - 不正なパーミッションのためCookieを削除")
            except Exception as e:
                logger.exception("check_permission_and_stop_order() - Cookie削除中にエラーが発生しました")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Cookie削除中にサーバーエラーが発生しました"
                )
            return False, None

    except HTTPException:
        raise  # 既に投げたHTTPExceptionはそのまま再スロー

    except Exception as e:
        logger.exception("check_permission_and_stop_order() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="権限と注文チェック中にサーバーエラーが発生しました"
        )

# # チェックする
# #@log_decorator
# async def check_permission_and_stop_order(request: Request, response: Response):
#     try:
#         ''' 権限と二重注文チェックを合体させた関数
#             - cookie permissionが1の場合に限り実行する。
#             - last_order_dateが存在していればTrueを返す
#             - それ以外の場合はFalseを返す
#         '''
#         # Cookieからpermissionを取得
#         permission = request.cookies.get("permission")
#         #print(f"cookie permission: {permission}")

#         if permission is None:
#             permission = '1'

#         if permission != '' and permission.isdigit():
#             permission = int(permission)
#         #print(f"permission: {permission}")

#         # permissionが1である場合のみ、二重注文（last_order_date）のチェックを行う
#         if permission == 1:
#             last_order = request.cookies.get("last_order_date")
#             if last_order is None:
#                 return False, None
#             else:
#                 logger.info(f"今日２度目の注文を阻止 - 最終注文日: {last_order}")
#                 logger.debug(f"result , last_order: {True , str(last_order)}")
#                 return True, last_order
#         else:
#             # Cookieを全部消す
#             delete_all_cookies(response)
#             return False, None

#     except KeyError as e:
#         logger.error(f"get_token_expires() - KeyError: {e}")
#     except ValueError:
#         logger.error(f"get_token_expires() - ValueError: {e}")
#     except Exception as e:
#         logger.error(f"get_token_expires() - 予期せぬエラーが発生しました: {e}")

        

# @log_decorator
# async def check_permission(request: Request, permits: list):
#     ''' 権限チェック '''
#     permission = request.cookies.get("permission")

#     # print(f"permission: {permission}")
#     if permission is None or permission == '':
#         permission = 0

#     if isinstance(permission, str) and permission.isdigit():
#         permission = int(permission)

#     # print(f"permits: {permits}")
#     if permission in permits:
#         return True

#     return False



@log_decorator
async def check_permission(request: Request, permits: list):
    """ 権限チェック処理（例外対応付き） """
    try:
        # permitsの型検証
        if not isinstance(permits, list) or not all(isinstance(p, int) for p in permits):
            logger.warning(f"check_permission() - permitsリストが不正: {permits}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="権限リスト（permits）が不正です"
            )

        # Cookieからpermission取得
        permission_str = request.cookies.get("permission")
        logger.debug(f"check_permission() - 取得したpermission: {permission_str}")

        # Cookieが存在しない or 空の場合はデフォルト0
        if not permission_str:
            logger.info("check_permission() - Cookieからpermissionが取得できません。デフォルト 0 を設定します。")
            permission = 0
        else:
            if not permission_str.isdigit():
                logger.warning(f"check_permission() - Cookieのpermissionが不正: {permission_str}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cookieのpermissionが不正です"
                )
            permission = int(permission_str)

        logger.debug(f"check_permission() - 解析後のpermission: {permission}")

        if permission in permits:
            logger.info(f"check_permission() - 許可されたパーミッション: {permission}")
            return True

        logger.info(f"check_permission() - 拒否されたパーミッション: {permission}")
        return False

    except HTTPException:
        raise  # 既に投げたものはそのまま返す

    except Exception as e:
        logger.exception("check_permission() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="権限チェック中にサーバーエラーが発生しました"
        )
