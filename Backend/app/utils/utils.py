# utils/utils.py
'''
    1. log_decorator(func):
    2. deprecated(func):

    3. get_naive_jst_now() -> datetime:
    4. get_today_datetime(offset: int = 0) -> date:
    5. get_today_date(offset: int = 0) -> datetime:
    6. get_datetime_range(days_ago: int) -> Tuple[datetime, datetime]:

    7. set_all_cookies(response: Response, user: Dict):
    8. get_all_cookies(request: Request) -> Optional[Dict[str, str]]:
    9. delete_all_cookies(response: Response):
    10. compare_expire_date(expires: str) -> bool:
    11. set_last_order(response: Response, last_order_date: datetime):
    12. check_order_duplex(request: Request):
    13. get_end_of_today(tz : timezone = None) -> datetime:
    14. get_token_expires(request: Request) -> str:

    15. check_permission_and_stop_order(request: Request, response: Response):
    16. check_permission(request: Request, permits: list):

'''
    
from datetime import datetime, timezone, timedelta, date

from venv import logger

from fastapi import Request, Response
from http.cookies import SimpleCookie

from functools import wraps
import functools
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




import pytz

@log_decorator
def get_naive_jst_now() -> datetime:
    """Asia/Tokyo の現在時刻を tzinfo なしで返す
    日付取得はasyncにする必要なし
    """
    time_now = datetime.strptime(
        datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S"),
        "%Y-%m-%d %H:%M:%S"
    )
    print(f"{time_now=}")
    return time_now


# @log_decorator
from fastapi import HTTPException, status



@log_decorator
def get_today_datetime(offset: int = 0) -> date:
    """
    JSTで offset 日前の0時0分0秒のナイーブな datetime を返す。
    例: offset=0 -> 今日の 00:00:00（タイムゾーンなし）
    """
    try:
        from log_unified import logger
        # 型と値の検証
        if not isinstance(offset, int):
            logger.warning(f"get_today_datetime() - 無効な offset: {offset}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="offset は 整数で指定してください"
            )

        tz = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(tz) + timedelta(days=offset)

        naive_datetime = datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            0, 0, 0
        )

        print(f"get_today_datetime() - 生成日時: {naive_datetime}")
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

# 今日の日付取得 update_datetime用
@log_decorator
def get_today_date(offset: int = 0) -> datetime:
    """
    今日の日付 (date型) を取得する関数。
    オプションで日数オフセットを指定可能。

    :param offset: 今日からのオフセット日数 (例: 昨日は -1, 明日は +1)
    :return: date型の日付 (時刻なし)

    d = get_today_date()
    print(d)  # 例: 2025-05-14

    # 文字列にしたい場合
    formatted = d.strftime("%Y/%m/%d")
    print(formatted)  # 例: 2025/05/14    
    """
    new_datetime = get_today_datetime() + timedelta(days=offset)
    result_date = new_datetime.date()

    print(f"get_today_date(): {result_date}")  # デバッグ出力

    return result_date


from typing import NamedTuple

class Period(NamedTuple):
    # 返却値が入れ替わるので、専用のクラスを作った
    start: datetime
    end: datetime

@log_decorator
async def get_datetime_range(days_ago: int) -> Period:
    """
    指定された days_ago に基づいて、期間の開始日時と終了日時を返す。
    返す datetime は tzinfo を持たない naive datetime。
    開始: 00:00:00、終了: 23:59:59
    """
    try:
        # 型と値の検証
        if not isinstance(days_ago, int) or days_ago < 0:
            logger.warning(f"get_datetime_range() - 無効な days_ago: {days_ago}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_ago は 0 以上の整数で指定してください"
            )

        # now = datetime.now(pytz.timezone("Asia/Tokyo"))
        now = get_naive_jst_now()
        start_target = now - timedelta(days=days_ago)
        end_target = now
        # # 00:00:00 と 23:59:59.999999 の datetime を作成
        # start_dt = f"{target_date.isoformat()} 00:00:00"
        # end_dt = f"{target_date.isoformat()} 23:59:59"
        # start_dt = datetime.combine(target_date, time.min)
        # end_dt = datetime.combine(target_date, time.max)
        start_dt = datetime(start_target.year, start_target.month, start_target.day, 0, 0, 0)
        end_dt   = datetime(end_target.year, end_target.month, end_target.day, 23, 59, 59)

        logger.debug(f"get_datetime_range() - start: {start_dt}, end: {end_dt}")

    except HTTPException:
        raise  # 既に投げた HTTPException はそのまま再スロー

    except (ValueError, TypeError) as e:
            logger.exception("get_datetime_range() - 型または値のエラー")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="期間計算中に不正なパラメータが指定されました"
            )

    except Exception as e:
        logger.exception("get_datetime_range() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="期間計算中にサーバーエラーが発生しました"
        )
    else:
        return Period(start_dt, end_dt)

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
# regist_completeで使っている
@log_decorator
def set_last_order(response: Response, last_order_date: datetime):
    ''' 最終注文日をCookieにセットしている '''
    today = get_today_date()
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

# Cookieによる二重注文拒否をやめた
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

from models.order import select_orders_by_user_at_date
from core.constants import ERROR_FORBIDDEN_SECOND_ORDER
from database.local_postgresql_database import endpoint
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

@log_decorator
async def check_order_duplex(request: Request):
    username = request.cookies.get("sub")
    today = get_today_date()
    today_orders = await select_orders_by_user_at_date(username, today)

    if today_orders:
        last_order = today_orders[0]
        logger.debug(f"check_order_duplex() - 既に注文が存在します: {last_order}")
        response = templates.TemplateResponse(
            "duplicate_order.html",
            {
                "request": request,
                "forbid_second_order_message": ERROR_FORBIDDEN_SECOND_ORDER,
                "last_order": last_order,
                "endpoint": endpoint
            },
            status_code=200
        )
        return True, response

    print("check_order_duplex() - 注文は存在しません")
    return False, None


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
