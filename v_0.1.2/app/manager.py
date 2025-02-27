# 管理者の権限チェック
from typing import Optional
from fastapi import HTTPException, Header, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from utils import check_permission, get_all_cookies, log_decorator
from sqlite_database import select_company_order
from services.order_view import order_table_view

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

from fastapi import APIRouter

manager_router = APIRouter()

@log_decorator
def check_manager_permission(request: Request):
    permission = request.cookies.get("permission")
    print(f"permission: {permission}")
    if permission in [2,99]:
        raise HTTPException(status_code=403, detail="Not Authorized")

# 会社お弁当担当者画面
# 注意：エンドポイントにprefix:managerはつけない
@manager_router.get("/today", response_class=HTMLResponse)
@log_decorator
async def manager_view(request: Request, response: Response, hx_request: Optional[str] = Header(None)):
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            print('cookie userなし')
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        check_permission(request, [2,99])

        #permission = cookies.get('permission')
        #if permission not in [2,99]:
            #raise HTTPException(status_code=403, detail="Not Authorized")

        # 昨日の全注文
        orders = await select_company_order(1)

        if orders is None:
            print('ordersなし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")

        return await order_table_view(request, response, orders, "manager_orders_today.html")

    except Exception as e:
        print(f"/manager_view Error: {str(e)}")
        return HTMLResponse(f"<html><p>エラーが発生しました: {str(e)}</p></html>")

