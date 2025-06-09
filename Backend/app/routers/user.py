# routers/user.py
# ../users/me
'''
    1. regist_complete(request: Request, response: Response): 
    2. get_user_context(request: Request, orders, user_id: int):
    3. show_order_cancel_form(request: Request, user_id: int):
    4. submit_order_cancel_form(request: Request, user_id: int, order_ids: str = Form(...)):
'''
from fastapi import Request, Response, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from utils.helper import redirect_error
from utils.utils import log_decorator
from utils.cookie_helper import get_all_cookies, set_last_order
from utils.permission_helper import check_permission


from models.user import select_user
from models.order import select_orders_by_user_ago, insert_order
from schemas.user_schemas import UserResponse
from services.order_view import order_table_view

from database.local_postgresql_database import endpoint
from log_unified import logger, log_order

templates = Jinja2Templates(directory="templates")
user_router = APIRouter()



# お弁当の注文完了　ユーザーのみ
# @log_decorator
@user_router.get(
    "/{user_id}/order_complete/",
    summary="お弁当の注文完了画面：一般ユーザー",
    description="一般ユーザーがお弁当を注文完了直後の画面",
    response_class=HTMLResponse,
    tags=["user"])
async def regist_complete(request: Request, response: Response, user_id: str):

    try:
        if not await check_permission(request, [1]): # ユーザーの権限
            return templates.TemplateResponse(
                "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)

        user: UserResponse = await select_user(cookies['sub'])
        if user is None:
            logger.error("ユーザーが見つかりません: sub=%s", cookies['sub'])
            return await redirect_error(request, "ユーザー情報の取得に失敗しました", None)

        await insert_order(
            user.company_id,
            user.username,
            user.shop_name,
            user.menu_id,
            amount=1
        )

        username = user.get_username()
        orders = await select_orders_by_user_ago(username, 7)

        if not orders:
            logger.error("注文が見つかりません: username=%s", username)
            return await redirect_error(request, "注文が見つかりません", None)

        order_count = len(orders) - 1
        last_order_date = orders[order_count].created_at

        set_last_order(response, last_order_date)  # ここで注文の重複を防止

        user_context = await get_user_context(request, orders, int(user.get_id()))

        return await order_table_view(request, response, orders, "order_complete.html", user_context)

    except Exception as e:
        logger.exception("予期せぬエラーが発生しました: %s", str(e))
        return await redirect_error(request, "注文確定中に予期せぬエラーが発生しました", e)



async def get_user_context(request: Request, orders, user_id: int):
    user_context = {
        'request': request,
        'base_url': endpoint,
    }
    order_context = {
        'orders': orders,
        'order_count': len(orders),
        "order_details": orders[-1].model_dump() if orders else None,
        "user_id": user_id
    }
    user_context.update(order_context)
    
    return user_context



# 注文キャンセル
# GET
# https://192.168.3.14:8000/user/1/order_cancel_form
@user_router.get(
    "/{user_id}/order_cancel_form",
    response_class=HTMLResponse,
    summary="注文キャンセルフォーム画面"
)
async def show_order_cancel_form(request: Request, user_id: int):
    try:
        logger.debug(f"show_order_cancel_form() - ユーザーID: {user_id}")
        return templates.TemplateResponse("order_cancel_form.html", {
            "request": request,
            "user_id": user_id
        })

    except Exception as e:
        logger.exception(f"show_order_cancel_form() - エラー発生: {e}")
        raise HTTPException(status_code=500, detail="注文キャンセルフォームの表示に失敗しました")


# POST
from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from database.local_postgresql_database import get_db
from schemas.order_schemas import CancelOrderRequest
from routers.order import set_order_cancel_by_user


@user_router.post(
    "/{user_id}/order_cancel_submit",
    response_class=HTMLResponse,
    summary="フォーム送信で注文キャンセル処理"
)
async def submit_order_cancel_form(
    request: Request,
    user_id: int,
    order_ids: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    try:
        
        
        # 入力はカンマ区切り: "101,102"
        order_id_list = [int(i.strip()) for i in order_ids.split(",") if i.strip().isdigit()]
        payload = CancelOrderRequest(order_ids=order_id_list, user_id=user_id)
        response = await set_order_cancel_by_user(payload=payload, session=session)


    except Exception as e:
        logger.exception(f"submit_order_cancel_form() - エラー発生: {e}")
        raise HTTPException(status_code=500, detail="注文キャンセルに失敗しました")
    else:
        log_order(
            "ORDER",
            f"全ての注文を削除しました。"
        )
        logger.debug(f"submit_order_cancel_form() - ユーザーID: {user_id}")
        return templates.TemplateResponse("order_cancel.html", {
            "request": request,
            "user_id": user_id,
            "canceled_order_ids": response.get("canceled_order_ids", [])
        })

# テスト方法
# curl -X POST "https://192.168.3.14:8000/user/2/order/cancel" \
#   -H "Content-Type: application/json" \
#   -d '{"order_ids": [14]}'




''' 開発中止する ユーザーのメニュー選択 '''
'''@user_router.post("/me", response_class=HTMLResponse, tags=["user"])
@user_router.get("/me", response_class=HTMLResponse, tags=["user"])
@log_decorator
async def get_user_shop_menu(request: Request, response: Response):
    # ユーザーお弁当屋のメニュー選択
    try:
        permits = [1, 2, 10, 99] # ユーザーの権限
        if await check_permission(request, permits) == False:
            return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="get_all_cookies()")

        # メニュー一覧
        menus = await select_all_menus(default_shop_name)
        #logger.debug(f"shop_name: {'shop01'}")

        if menus is None:
            logger.debug('get_user_shop_menu - menusなし')

            return HTMLResponse("<html><p>メニューは0件です</p></html>")

        logger.debug(f"menus取得 {menus}")

        return await menu_cards_view(request, response, menus, "shop_menu.html")

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/get_user_shop_menu()",
            f"Error: {str(e)}")
'''

# お弁当の注文完了　ユーザーのみ
# @log_decorator
@user_router.get(
    "/{user_id}/order_cancel_complete/",
    summary="お弁当の注文キャンセル完了画面：一般ユーザー",
    description="一般ユーザーがお弁当を注文キャンセル完了直後の画面",
    response_class=HTMLResponse,
    tags=["user"])
async def cancel_complete(request: Request, response: Response, user_id: str):

    try:
        if not await check_permission(request, [1]): # ユーザーの権限
            return templates.TemplateResponse(
                "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)

        user: UserResponse = await select_user(cookies['sub'])
        if user is None:
            logger.error("ユーザーが見つかりません: sub=%s", cookies['sub'])
            return await redirect_error(request, "ユーザー情報の取得に失敗しました", None)

        # 最新の注文をキャンセルする
            
        # await insert_order(
        #     user.company_id,
        #     user.username,
        #     user.shop_name,
        #     user.menu_id,
        #     amount=1
        # )

        username = user.get_username()
        orders = await select_orders_by_user_ago(username, 7)

        if not orders:
            logger.error("注文が見つかりません: username=%s", username)
            return await redirect_error(request, "注文が見つかりません", None)

        order_count = len(orders) - 1
        last_order_date = orders[order_count].created_at
        set_last_order(response, last_order_date)  # ここで注文の重複を防止

        user_context = await get_user_context(request, orders, int(user.get_id()))

        return await order_table_view(request, response, orders, "order_complete.html", user_context)

    except Exception as e:
        logger.exception("予期せぬエラーが発生しました: %s", str(e))
        return await redirect_error(request, "注文確定中に予期せぬエラーが発生しました", e)
