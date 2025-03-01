# 店舗の権限チェック
import json
from typing import Optional
from fastapi import HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi import Header

from utils.exception import CustomException

templates = Jinja2Templates(directory="templates")

from main import order_table_view
from database.sqlite_database import select_shop_order, select_user
from utils.utils import deprecated, get_all_cookies, log_decorator


from fastapi import APIRouter

shop_router = APIRouter()

# お店の権限チェック
@deprecated
@log_decorator
def check_store_permission(request: Request):
    permission = request.cookies.get("permission")
    #print(f"check_store_permission: {permission}")
    if permission is None:
        raise CustomException(403, "Permission Data is not Contained")
        #raise HTTPException(status_code=403, detail="Permission Data is not Contained")
    if permission == [10,99]:
        raise CustomException(403, "Not Authorized")
        #raise HTTPException(status_code=403, detail="Not Authorized")

# お弁当屋の注文確認
# shops/todayになる
@shop_router.post("/today", response_class=HTMLResponse, tags=["shops"])
@shop_router.get("/today", response_class=HTMLResponse, tags=["shops"])
@log_decorator
async def shop_today_order(request: Request, response: Response, hx_request: Optional[str] = Header(None)):
    
    try:
        #check_permission(request, [10,99])
        check_store_permission(request)

        cookies = get_all_cookies(request)
        if not cookies:
            #print('cookie userなし')
            raise CustomException(400, "cookie よりユーザー情報が取得できませんでした。")
            #return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)
        
        # 昨日の全注文
        orders = await select_shop_order('shop01')
        
        if orders is None:
            print('ordersなし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")

        main_view = "store_orders_today.html"
        return await order_table_view(request, response, orders, main_view)

    except Exception as e:
        raise CustomException(400, f"/shop_today_order Error: {str(e)}")
        #print(f"/shop_today_order Error: {str(e)}")
        #return HTMLResponse(f"<html><p>エラーが発生しました: {str(e)}</p></html>")

# 注文情報を取得する
# 例 https://127.0.0.1:8000/today/order_json?days_ago=-5
@shop_router.get("/today/order_json",response_class=HTMLResponse, tags=["shops"]) 
@log_decorator
async def order_json(request: Request, days_ago: str = Query(None)):
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            #return HTMLResponse("<html><p>ユーザー情報が取得できませんでした。</p></html>")
            #return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)
            raise CustomException(400, "cookie よりユーザー情報が取得できませんでした。")


        # 注文追加
        user = await select_user(cookies['sub'])

        if user is None:
            raise CustomException(400, "select_user よりユーザー情報が取得できませんでした。")
            #print(f"user:{user} 取得に失敗しました")
            #return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        if days_ago is not None:
            print(f"days_ago: {int(days_ago)}")

        #print(f"days_ago: {days_ago}")
        # 履歴取得
        if days_ago is None:
            #print("全履歴を取得する") 
            orders = await select_shop_order(user.shop_name)
        elif days_ago.isdigit() or (days_ago.startswith('-') and days_ago[1:].isdigit()):
            #print(f"{days_ago} 日前までの履歴を取得する")
            orders = await select_shop_order(user.shop_name, days_ago)
        else:
            raise CustomException(400, "days_ago の値が無効です")
            #return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

        if not orders:
            raise CustomException(400, "len(orders)=0 注文が見つかりません。")
            #print("No orders found or error occurred.")
            #return JSONResponse({"message": "注文が見つかりません。"}, status_code=404)

        # 日時で逆順
        orders.sort(key=lambda x: x.created_at, reverse=True)

        #print("ここまできた 3")
        #for order in orders:
        #    print(order.model_dump_json())

        #print("ここまできた 4")
 
        orders_dict = [order.model_dump() for order in orders]
        orders_json = json.dumps(orders_dict, default=str)  # ← datetime を文字列に変換

        return JSONResponse(content=json.loads(orders_json))  # JSON をパースしてレスポンス
    
    except Exception as e:
        raise CustomException(500, f"/order_json Error: {str(e)}")
        #orders = []
        #print(f"/order_json Error: {str(e)}")
        #return JSONResponse({"error": f"エラーが発生しました: {str(e)}"}, status_code=500)
