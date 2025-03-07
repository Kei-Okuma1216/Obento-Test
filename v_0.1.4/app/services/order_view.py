# 管理者の権限チェック
import json
from venv import logger
from fastapi import HTTPException, APIRouter, Query, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from database.sqlite_database import select_shop_order, select_user
from main import get_all_cookies
templates = Jinja2Templates(directory="templates")
from database.sqlite_database import CustomException
from utils.utils import log_decorator 


view_router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


# 注文一覧テーブル表示
@log_decorator
async def order_table_view(request: Request, response: Response, orders, redirect_url: str):
    try:
        #print(f"ordersあり")
   
        # ordersリストをin-placeで降順にソート
        orders.sort(key=lambda x: x.order_id, reverse=True)

        # ソート結果を確認
        #for order in orders:
            #print(order)
        #print("ここまできた 1")
        context = {'request': request, 'orders': orders}
        inner_table = "table.html"

        templates.TemplateResponse(inner_table,context)
        #print("ここまできた 2")
        template_response = templates.TemplateResponse(
            redirect_url, context)
        #print("ここまできた 3")
        # 必須！　Set-CookieヘッダーがNoneでないことを確認
        set_cookie_header = response.headers.get("Set-Cookie")
        #print("ここまできた 4")
        if set_cookie_header is not None:
            template_response.headers["Set-Cookie"] = set_cookie_header
        #print("ここまできた 5")
        return template_response

    except HTTPException as e:
        raise HTTPException(e.status_code, e.detail)
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/order_table_view()",
            f"Error: {str(e)}")
        #print(f"/order_table_view Error: {str(e)}")
        #return JSONResponse({"message": "エラーが発生しました"},
        #                    e.status_code)


# 注文情報を取得する
# 例 /order_json?days_ago=-5
#@app.get("/order_json",response_class=HTMLResponse) 
@log_decorator
async def get_order_json(request: Request, days_ago: str = Query(None)): 
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            #return HTMLResponse("<html><p>ユーザー情報が取得できませんでした。</p></html>")
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        # 注文追加
        user = await select_user(cookies['sub'])

        if user is None:
            logger.debug(f"user:{user} 取得に失敗しました")
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        if days_ago is not None:
            logger.debug(f"days_ago: {int(days_ago)}")

        #print(f"days_ago: {days_ago}")
        # 履歴取得
        if days_ago is None:
            logger.debug("全履歴を取得する") 
            orders = await select_shop_order(user.shop_name)
        elif days_ago.isdigit() or (days_ago.startswith('-') and days_ago[1:].isdigit()):
            logger.debug(f"{days_ago} 日前までの履歴を取得する")
            orders = await select_shop_order(user.shop_name, days_ago)
        else:
            return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

        if not orders:
            logger.info("No orders found or error occurred.")
            return JSONResponse({"message": "注文が見つかりません。"}, status_code=404)

        # 日時で逆順
        orders.sort(key=lambda x: x.created_at, reverse=True)

        #print("ここまできた 3")
        for order in orders:
            logger.debug(order.model_dump_json())

        #print("ここまできた 4")
 
        orders_dict = [order.model_dump() for order in orders]
        orders_json = json.dumps(orders_dict, default=str)  # ← datetime を文字列に変換

        return JSONResponse(content=json.loads(orders_json))  # JSON をパースしてレスポンス
    
    except Exception as e:
        orders = []
        logger.warning(f"/order_json Error: {str(e)}")
        return JSONResponse({"error": f"エラーが発生しました: {str(e)}"}, status_code=500)
