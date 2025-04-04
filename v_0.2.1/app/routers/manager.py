# manager.py
# ../manager/meになる
from venv import logger
from fastapi import Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse, RedirectResponse

from utils.exception import CookieException, CustomException
from utils.utils import check_permission, deprecated, get_all_cookies, log_decorator
from database.sqlite_database import select_company_order, select_company_order2
from services.order_view import order_table_view

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")


manager_router = APIRouter()

@deprecated
@log_decorator
def check_manager_permission(request: Request):
    permission = request.cookies.get("permission")
    #print(f"permission: {permission}")
    if permission in [2,99]:
        raise CustomException(
            status.HTTP_403_FORBIDDEN,
            "check_manager_permission()",
            f"Not Authorized permission={permission}")


# 会社お弁当担当者画面
# 注意：エンドポイントにprefix:managerはつけない
@manager_router.get("/me", response_class=HTMLResponse, tags=["manager"])
@log_decorator
async def manager_view(request: Request, response: Response):
    try:
        if await check_permission(request, [2, 99]) == False:
            return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="manager_view()")

        # 会社の全注文
        orders = await select_company_order2(company_id=1)

        if orders is None:
            logger.debug('ordersなし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")


        # 表示用データの作成
        context = {
            'request': request,
            'base_url': "https://192.168.3.19:8000",
        }
        # 注文一覧タブ用のデータ
        order_context = {
            'orders': orders,
            'order_count': len(orders),
            "order_details": orders[0].model_dump() if orders else None
        }
        
        fax_context = {
            "shop_name": "はーとあーす勝谷",
            "menu_name": "お昼のお弁当",
            "price": 450,
            "order_count": 6,
            "total_amount": 450*6,
            "facility_name": "テンシステム",
            "POC": "林"
        }
        context.update(order_context)
        context.update(fax_context)

        return await order_table_view(request, response, orders, "manager.html", context)

    except CookieException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            "/manager_view()",
            f"Error: {str(e)}")


@manager_router.get("/me/fax_order_sheet", response_class=HTMLResponse, tags=["manager"])
@log_decorator
async def fax_order_sheet_view(request: Request):

    fax_context = {
         "shop_name": request.query_params.get("shop_name"),
         "menu_name": request.query_params.get("menu_name"),
         "price": request.query_params.get("price"),
         "order_count": request.query_params.get("order_count"),
         "total_amount": request.query_params.get("total_amount"),
         "facility_name": request.query_params.get("facility_name"),
         "POC": request.query_params.get("POC"),
         "delivery_year": request.query_params.get("delivery_year"),
         "delivery_month": request.query_params.get("delivery_month"),
         "delivery_day": request.query_params.get("delivery_day"),
         "delivery_weekday": request.query_params.get("delivery_weekday")
    }

    return templates.TemplateResponse("fax_order_sheet.html", {"request": request, **fax_context})

