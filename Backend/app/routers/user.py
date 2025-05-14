# routers/user.py
# ../users/me
'''
    1. regist_complete(request: Request, response: Response): 
    2. get_user_shop_menu(request: Request, response: Response):
'''
from fastapi import Request, Response, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from utils.helper import redirect_error
from utils.utils import get_all_cookies, log_decorator, check_permission, set_last_order
from models.user import select_user
from models.order import select_orders_by_user_ago, insert_order
from schemas.user_schemas import UserResponse
from services.order_view import order_table_view

from database.local_postgresql_database import endpoint
from log_unified import logger

templates = Jinja2Templates(directory="templates")
user_router = APIRouter()



# お弁当の注文完了　ユーザーのみ
@user_router.get("/order_complete", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def regist_complete(request: Request, response: Response):
    try:
        permits = [1, 2, 10, 99]  # ユーザーの権限
        if not await check_permission(request, permits):
            return templates.TemplateResponse("Unauthorized.html", {"request": request})

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

        user_context = await get_user_context(request, orders)

        return await order_table_view(request, response, orders, "order_complete.html", user_context)

    except Exception as e:
        logger.exception("予期せぬエラーが発生しました: %s", str(e))
        return await redirect_error(request, "注文確定中に予期せぬエラーが発生しました", e)



async def get_user_context(request: Request, orders):
    user_context = {
        'request': request,
        'base_url': endpoint,
    }
    order_context = {
        'orders': orders,
        'order_count': len(orders),
        "order_details": orders[-1].model_dump() if orders else None
    }
    user_context.update(order_context)
    return user_context


''' 開発中止する ユーザーのメニュー選択 '''
'''@user_router.post("/me", response_class=HTMLResponse, tags=["users"])
@user_router.get("/me", response_class=HTMLResponse, tags=["users"])
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