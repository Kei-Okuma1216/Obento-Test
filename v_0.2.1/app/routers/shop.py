# routers/shop.py
# ../shops/meになる
'''
    1. shop_view(request: Request, response: Response):
    2. get_shop_context(request: Request, orders):
    3. order_json(request: Request, days_ago: str = Query("0")):
'''
from fastapi import Query, Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from venv import logger

from utils.utils import get_all_cookies, check_permission, log_decorator
from utils.exception import SQLException, CookieException, CustomException
from services.order_view import order_table_view, get_order_json
from models.order import select_orders_by_shop_all
from database.local_postgresql_database import endpoint, default_shop_name


templates = Jinja2Templates(directory="templates")

shop_router = APIRouter()




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

        shop_context = await get_shop_context(request, orders)

        return await order_table_view(response, orders, "shop.html", shop_context)


    except (CookieException, SQLException) as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/shop_view()",
            f"Error: {str(e)}")


async def get_shop_context(request: Request, orders):
        # 備考：ここはtarget_urlをcontextに入れる改善が必要
        # 更に、order_table_view()も引数を2個にできる(response, shop_context)
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


@shop_router.get("/me/order_json",response_class=HTMLResponse, tags=["shops"]) 
@log_decorator
async def order_json(request: Request, days_ago: str = Query("0")):
    # services/order_view.pyにある
    return await get_order_json(request, days_ago)
