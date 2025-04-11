# shop.py
# ../shops/meになる
'''
    1. shop_view(request: Request, response: Response):
        service.order_table_view(request, response, orders, "shop.html")を呼び出す。
    2. order_json(request: Request, days_ago: str = Query("0")):
        get_order_json(request, days_ago)を呼び出す。
'''

from fastapi import Query, Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.utils import get_all_cookies, check_permission, log_decorator
from utils.exception import SQLException, CookieException, CustomException
from services.order_view import order_table_view, get_order_json

templates = Jinja2Templates(directory="templates")

shop_router = APIRouter()

#from database.sqlite_database import select_shop_order
from database.order import select_orders_by_shop_all
from database.sqlalchemy_database import default_shop_name, endpoint
from venv import logger

@shop_router.post("/me", response_class=HTMLResponse, tags=["shops"])
@shop_router.get("/me", response_class=HTMLResponse, tags=["shops"])
@log_decorator
async def shop_view(request: Request, response: Response):
    # お弁当屋の注文確認
    try:
        permits = [10, 99]
        if await check_permission(request, permits) == False:
            return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="get_all_cookies()")

        orders = await select_orders_by_shop_all(default_shop_name)

        if orders is None:
            logger.debug('shop_view - ordersなし')

            return HTMLResponse("<html><p>注文は0件です</p></html>")

        shop_context = {
            'request': request,
            'base_url': endpoint,
        }
        return await order_table_view(request, response, orders, "shop.html", shop_context)

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/shop_view()",
            f"Error: {str(e)}")

@shop_router.get("/me/order_json",response_class=HTMLResponse, tags=["shops"]) 
@log_decorator
async def order_json(request: Request, days_ago: str = Query("0")):
    return await get_order_json(request, days_ago)
