# utils/permission_helper.py
# 備考：Cookieによる二重注文判定はやめてDB判定にした。
'''
    1. check_permission_and_stop_order(request: Request, response: Response)
    2. check_permission(request: Request, permits: list)  
    3. get_last_order(request: Request)
'''
from fastapi import HTTPException, Request, Response, status

from utils.utils import log_decorator
from utils.date_utils import get_today_date
from utils.cookie_helper import delete_all_cookies

from core.constants import ERROR_FORBIDDEN_SECOND_ORDER
from models.order import select_orders_by_user_at_date
from database.local_postgresql_database import endpoint

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

from log_unified import logger

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
        # logger.debug(f"check_permission() - 取得したpermission: {permission_str}")

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

        # logger.debug(f"check_permission() - 解析後のpermission: {permission}")

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


@log_decorator
async def get_last_order(request: Request):
    username = request.cookies.get("sub") # ログオフしたら再注文できる　それと登録なしユーザーも返却値が発生する。

    if not username:
        # ログを出して処理を止める
        logger.error("Cookieから username が取得できませんでした。")
        return False, templates.TemplateResponse("error.html", {"request": request, "error": "認証情報が不正です。"})

    today = get_today_date()
    today_orders = await select_orders_by_user_at_date(username, today)

    if today_orders:
        last_order = today_orders[0]
        logger.warning(f"- 既に注文が存在します: {last_order}")
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

    logger.debug("get_last_order() - 注文は存在しません")
    return False, None



