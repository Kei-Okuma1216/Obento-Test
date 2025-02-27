# 店舗の権限チェック
from typing import Optional
from fastapi import HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi import Header

templates = Jinja2Templates(directory="templates")

from main import order_table_view
from sqlite_database import select_shop_order
from utils import get_all_cookies, log_decorator


from fastapi import APIRouter

shop_router = APIRouter()

# お店の権限チェック
@log_decorator
def check_store_permission(request: Request):
    permission = request.cookies.get("permission")
    #print(f"check_store_permission: {permission}")
    if permission is None:
        raise HTTPException(status_code=403, detail="Permission Data is not Contained")
    if permission == [10,99]:
        raise HTTPException(status_code=403, detail="Not Authorized")

# お弁当屋の注文確認
@shop_router.post("/today", response_class=HTMLResponse, tags=["shops"])
@shop_router.get("/today", response_class=HTMLResponse, tags=["shops"])
@log_decorator
async def shop_today_order(request: Request, response: Response, hx_request: Optional[str] = Header(None)):
    
    try:
        check_store_permission(request)

        cookies = get_all_cookies(request)
        if not cookies:
            print('cookie userなし')
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)
        
        # 昨日の全注文
        orders = await select_shop_order('shop01')
        
        if orders is None:
            print('ordersなし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")

        main_view = "store_orders_today.html"
        return await order_table_view(request, response, orders, main_view)

    except Exception as e:
        print(f"/shop_today_order Error: {str(e)}")
        return HTMLResponse(f"<html><p>エラーが発生しました: {str(e)}</p></html>")

