# routers/shop.py
# ../shops/4になる
# 引数が固定順(パスパラメータが無い順)に並べている
'''
    1. order_json_me(request: Request, days_ago: str = Query("0")):
    2. order_json_by_id(request: Request, shop_id: str, days_ago: str = Query("0")):
    3. shop_view(request: Request, response: Response, shop_id: int):
    4. get_shop_context(request: Request, orders):
    5. shop_summary_bridge(shop_id: int):
'''
from fastapi import HTTPException, Query, Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse
from venv import logger

from utils.helper import redirect_login_failure, redirect_unauthorized
from utils.utils import get_all_cookies, check_permission, log_decorator


from models.order import select_orders_by_shop_all

from database.local_postgresql_database import endpoint, default_shop_name
from core.constants import ERROR_ILLEGAL_COOKIE

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

shop_router = APIRouter()


from services.order_view import get_order_json
from models.user import select_user_by_id

# JSON/me注文情報を取得する
@shop_router.get(
    "/me/order_json",
    summary="JSON注文情報を取得する：指定店舗ユーザー",
    description="shop_idとdays_agoに基づいて注文情報をJSON形式で返す。",
    tags=["shop"],
    include_in_schema=False
)
@log_decorator
async def order_json_me(request: Request, days_ago: str = Query("0")):
    return await get_order_json(request, days_ago)


# JSON注文情報を取得する
@shop_router.get(
    "/{shop_id:int}/order_json",
    summary="JSON注文情報を取得する：指定店舗ユーザー",
    description="shop_idとdays_agoに基づいて注文情報をJSON形式で返す。",
    response_class=HTMLResponse,
    tags=["shop"]
)
@log_decorator
async def order_json_by_id(request: Request, shop_id: str, days_ago: str = Query("0")):
    try:
        user_info = await select_user_by_id(int(shop_id))
        if user_info is None:
            raise HTTPException(status_code=404, detail="店舗ユーザーが見つかりません")

        return await get_order_json(request, days_ago, shop_code=user_info.username)
        # shop_code = user_info.username

        # # get_order_json を拡張 or 新たに shop_code 対応関数を用意する
        # return await get_order_json(request, days_ago, shop_code=shop_code)
    except HTTPException as e:
        logger.exception(f"order_json - HTTPException: {e.detail}")
        return HTMLResponse(f"エラー: {e.detail}", status_code=e.status_code)

    except Exception as e:
        logger.exception("order_json - 予期せぬエラー")
        return HTMLResponse("注文データ取得中に予期せぬエラーが発生しました", status_code=500)




from models.user import select_user_by_id
from services.order_view import order_table_view

# 店舗メイン画面
@shop_router.get(
    "/{shop_id:int}",
    summary="メイン画面：店舗ユーザー",
    description="shop_id設定よりorder_table_view()を表示する。",
    response_class=HTMLResponse,
    tags=["shop"])
@log_decorator
async def shop_view(request: Request, response: Response, shop_id: int):
    try:
        # 🚨 不正なID防御（Noneや非数値チェック）
        # if not shop_id or shop_id.lower() == "none" or not shop_id.isdigit():
        if not shop_id:
            logger.error("不正な shop_id が指定されました")
            return HTMLResponse("<html><p>不正な店舗IDが指定されました</p></html>", status_code=400)
        
        # 権限確認
        if await check_permission(request, [10]) == False:
            return redirect_unauthorized(request, "店舗ユーザー権限がありません。")

        # ユーザー情報取得
        user_info = await select_user_by_id(shop_id)
        if user_info is None:
            logger.warning(f"ユーザーID {shop_id} が見つかりません")
            return HTMLResponse("<html><p>ユーザー情報が見つかりません</p></html>")

        # username（shop01）を取得
        shop_code = user_info.username

        orders = await select_orders_by_shop_all(shop_code)
        if orders is None:
            logger.debug('shop_view - 注文がありません')
            return HTMLResponse("<html><p>注文は0件です</p></html>")


        shop_context = await get_shop_context(request, orders)

        # username（shop01）を取得
        shop_code = user_info.username

        shop_context.update({"username": shop_code, "shop_id": shop_id})

        return await order_table_view(request, response, orders, "shop.html", shop_context)

    except HTTPException as e:
        logger.exception(f"HTTPException: {e.detail}")
        return redirect_login_failure(request, e.detail)
    except Exception as e:
        logger.exception("shop_viewで予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注文情報の取得中にサーバーエラーが発生しました"
        )

# 店舗メイン画面コンテキスト取得
async def get_shop_context(request: Request, orders):
    try:
        shop_context = {
            'request': request,
            'base_url': endpoint,
        }
        order_context = {
            'orders': orders,
            'order_count': len(orders),
            "order_details": orders[0].model_dump() if orders else None
        }

        shop_context.update(order_context)
        return shop_context

    except (AttributeError, TypeError) as e:
        logger.exception("get_shop_context - 注文データ形式不正")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="注文データが不正です"
        )
    except Exception as e:
        logger.exception("get_shop_context - 予期せぬエラー")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注文情報取得中にサーバーエラーが発生しました"
        )


from routers.order import get_orders_summary_by_shop

@shop_router.get(
    "/{shop_id}/summary",
    summary="注文概要取得へのリダイレクト用：店舗ユーザー",
    description="店舗の注文概要取得へのリダイレクト用。",
    include_in_schema=False,
    tags=["shop"]
)
async def shop_summary_bridge(shop_id: int):
    # 注意：ここは更にリダイレクトしている
    return await get_orders_summary_by_shop(shop_id)
