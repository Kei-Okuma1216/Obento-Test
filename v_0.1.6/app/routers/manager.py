# manager.py
from venv import logger
from fastapi import Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse

from utils.exception import CookieException, CustomException
from utils.utils import get_all_cookies, log_decorator
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
        cookies = get_all_cookies(request)
        if not cookies:
            logger.debug('cookie userなし')
            raise CookieException(method_name="manager_view()")

        check_manager_permission(request)

        # 昨日の全注文
        orders = await select_company_order(company_id=1)

        if orders is None:
            logger.debug('ordersなし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")
            #return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        target_url = "manager_orders_today.html"
        return await order_table_view(request, response, orders, target_url)

    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            "/manager_view()",
            f"Error: {str(e)}")

