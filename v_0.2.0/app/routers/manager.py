# manager.py
from venv import logger
from fastapi import Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse

from utils.exception import CookieException, CustomException
from utils.utils import check_permission, get_all_cookies, log_decorator
from database.sqlite_database import select_company_order
from services.order_view import order_table_view

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")


manager_router = APIRouter()

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

        # 昨日の全注文
        orders = await select_company_order(company_id=1)

        if orders is None:
            logger.debug('ordersなし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")

        target_url = "manager.html"
        return await order_table_view(request, response, orders, target_url)

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
    # 仮にハードコートしておく
    fax_context = {
         "shop_name": "はーとあーす勝谷",
         "menu_name": "お昼のお弁当",
         "price": 450,
         "order_count": 3,
         "total_amount": 2700,  # 例: 450 * 6 など、実際の計算結果
         "facility_name": "テンシステム",
         "POC": "林"
    }
    return templates.TemplateResponse("fax_order_sheet.html", {"request": request, **fax_context})
