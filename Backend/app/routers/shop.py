# routers/shop.py
# ../shops/4になる
# 引数が固定順(パスパラメータが無い順)に並べている
'''
    1. order_json(request: Request, days_ago: str = Query("0")):

    2. filter_order_logs(background_tasks: BackgroundTasks, shop: str = Query(...)):

    3. shop_view(request: Request, response: Response, shop_id: str):
    4. get_shop_context(request: Request, orders):
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

# JSON注文情報を取得する
@shop_router.get(
    "/me/order_json",
    summary="JSON注文情報を取得する：店舗ユーザー",
    description="days_ago:intより指定日数前の注文情報を取得後、JSON形式で表示する。",
    response_class=HTMLResponse,
    tags=["shop"]
)
@log_decorator
async def order_json(request: Request, days_ago: str = Query("0")):
    try:
        return await get_order_json(request, days_ago)

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
    "/{shop_id}",
    summary="メイン画面：店舗ユーザー",
    description="shop_id設定よりorder_table_view()を表示する。",
    response_class=HTMLResponse,
    tags=["shop"])
@log_decorator
async def shop_view(request: Request, response: Response, shop_id: str):
    try:
        # 🚨 不正なID防御（Noneや非数値チェック）
        if not shop_id or shop_id.lower() == "none" or not shop_id.isdigit():
            logger.error("不正な shop_id が指定されました")
            return HTMLResponse("<html><p>不正な店舗IDが指定されました</p></html>", status_code=400)
        
        # 権限確認
        if await check_permission(request, [10]) == False:
            return redirect_unauthorized(request, "店舗ユーザー権限がありません。")

        # ユーザー情報取得
        user_info = await select_user_by_id(int(shop_id))
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
