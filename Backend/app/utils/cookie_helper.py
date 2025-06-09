# utils.cookie_helper.py
'''
    Cookieの設定、取得、削除を行うヘルパー関数群
    1. set_all_cookies(response: Response, user: Dict):
    2. get_all_cookies(request: Request) -> Optional[Dict[str, str]]:
    3. delete_all_cookies(response: Response):
    4. compare_expire_date(expires: str) -> bool:    
    5. set_last_order(response: Response, last_order_date: datetime):
'''
from fastapi import HTTPException, Request, Response, status

from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from typing import Dict, Optional

from utils.decorator import log_decorator
from log_unified import logger


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


from utils.date_utils import get_today_date
import pytz

# 二重注文の禁止
# 備考：regist_completeで使っている
@log_decorator
def set_last_order(response: Response, last_order_date: datetime):
    ''' 最終注文日をCookieにセットしている '''
    today = get_today_date()
    end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
    end_time = int(end_of_day.timestamp())

    current = datetime.strptime(datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S"),
        "%Y-%m-%d %H:%M:%S")#get_naive_jst_now()
    current_time = int(current.timestamp())

    future_time = end_time - current_time

    logger.debug(f"last_order_date: {last_order_date}")
    logger.debug(f"future_time: {future_time}")

    response.set_cookie(
        key="last_order_date", value=last_order_date,
        max_age=future_time, httponly=True)
    logger.debug("set_last_order() # 期限を本日の23:59:59にした")


