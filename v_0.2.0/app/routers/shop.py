# shop.py
# ../shops/meになる
from venv import logger
from fastapi import Query, Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database.sqlite_database import SQLException, select_shop_order
from utils.utils import get_all_cookies, check_permission, log_decorator
from utils.exception import CookieException, CustomException
from services.order_view import order_table_view, get_order_json

templates = Jinja2Templates(directory="templates")

shop_router = APIRouter()

@shop_router.post("/me", response_class=HTMLResponse, tags=["shops"])
@shop_router.get("/me", response_class=HTMLResponse, tags=["shops"])
@log_decorator
async def shop_today_order(request: Request, response: Response):
    # お弁当屋の注文確認
    try:
        if await check_permission(request, [10, 99]) == False:
            return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="get_all_cookies()")

        orders = await select_shop_order('shop01')

        if orders is None:
            logger.debug('shop_today_order - ordersなし')

            return HTMLResponse("<html><p>注文は0件です</p></html>")

        return await order_table_view(request, response, orders, "shop_main.html")

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/shop_today_order()",
            f"Error: {str(e)}")

@shop_router.get("/me/order_json",response_class=HTMLResponse, tags=["shops"]) 
@log_decorator
async def order_json(request: Request, days_ago: str = Query("0")):
    return await get_order_json(request, days_ago)
