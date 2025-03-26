# user.py
# users/me
from fastapi import HTTPException, Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database.sqlite_database import select_menu, select_shop_order, select_user, insert_order
from schemas.schemas import UserResponse
from utils.helper import redirect_error
from utils.utils import get_all_cookies, log_decorator, check_permission, prevent_order_twice
from utils.exception import CustomException, CookieException, SQLException
from log_config import logger

from services.menu_view import menu_cards_view
from services.order_view import order_table_view

templates = Jinja2Templates(directory="templates")

user_router = APIRouter()


# お弁当の注文完了　ユーザーのみ
@user_router.get("/order_complete",response_class=HTMLResponse, tags=["users"]) 
@log_decorator
async def regist_complete(request: Request, response: Response): 
    try:
        cookies = get_all_cookies(request)
        print("こっちがuser.py")
        user: UserResponse = await select_user(cookies['sub'])

        if user is None:
            raise SQLException("regist_complete()")

        await insert_order(
            user.company_id,
            user.username,
            user.shop_name,
            user.menu_id,
            amount=1)

        orders = await select_shop_order(
            user.shop_name, -7, user.username)

        #logger.debug(f"orders: {orders}")
        if orders is None or len(orders) == 0:
            logger.debug("No orders found or error occurred.")
            raise CustomException(
                status.HTTP_400_BAD_REQUEST,
                "regist_complete()",
                "注文が見つかりません")

        #await show_all_orders()
        order_count = len(orders) - 1
        last_order_date = orders[order_count].created_at
        #last_order_date = orders[0].created_at # DESCの場合
        prevent_order_twice(response, last_order_date)

        return await order_table_view(
            request, response, orders, "order_complete.html")

    except (SQLException, HTTPException) as e:
        return redirect_error(request, "注文確定に失敗しました", e)
    except Exception as e:
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "regist_complete()",
            f"予期せぬエラーが発生しました: {str(e)}")



''' 開発中止する ユーザーのメニュー選択 '''
@user_router.post("/me", response_class=HTMLResponse, tags=["users"])
@user_router.get("/me", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def get_user_shop_menu(request: Request, response: Response):
    # ユーザーお弁当屋のメニュー選択
    try:
        if await check_permission(request, [1, 2, 10, 99]) == False:
            return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="get_all_cookies()")

        # メニュー一覧
        menus = await select_menu('shop01')
        logger.debug(f"shop_name: {'shop01'}")

        if menus is None:
            logger.debug('get_user_shop_menu - menusなし')

            return HTMLResponse("<html><p>メニューは0件です</p></html>")

        logger.debug(f"menus取得 {menus}")

        main_view = "shop_menu.html"
        return await menu_cards_view(request, response, menus, main_view)

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/shop_today_order()",
            f"Error: {str(e)}")