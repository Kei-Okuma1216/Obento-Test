# 店舗の権限チェック
from venv import logger
from fastapi import Query, Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import json

from database.sqlite_database import SQLException, select_shop_order, select_user
from utils.utils import deprecated, get_all_cookies, log_decorator
from utils.exception import CookieException, CustomException
from main import order_table_view

templates = Jinja2Templates(directory="templates")

shop_router = APIRouter()


# お店の権限チェック
@deprecated
@log_decorator
def check_store_permission(request: Request):
    permission = request.cookies.get("permission")
    logger.debug(f"check_store_permission: {permission}")
    if permission is None:
        raise CustomException(
            status.HTTP_403_FORBIDDEN,
            "order_json()",
            "Permission Data is not Contained")

    if permission == [10,99]:
        raise CustomException(status.HTTP_401_UNAUTHORIZED, "Not Authorized")

# お弁当屋の注文確認
# shops/todayになる
@shop_router.post("/me", response_class=HTMLResponse, tags=["shops"])
@shop_router.get("/me", response_class=HTMLResponse, tags=["shops"])
@log_decorator
async def shop_today_order(request: Request, response: Response):

    try:
        check_store_permission(request)

        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="get_all_cookies()")
        
        # 昨日の全注文
        orders = await select_shop_order('shop01')
        
        if orders is None:
            logger.debug('shop_today_order - ordersなし')

            return HTMLResponse("<html><p>注文は0件です</p></html>")

        main_view = "store_orders_today.html"
        return await order_table_view(request, response, orders, main_view)

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/shop_today_order()",
            f"Error: {str(e)}")
        #print(f"/shop_today_order Error: {str(e)}")
        #return HTMLResponse(f"<html><p>エラーが発生しました: {str(e)}</p></html>")

from services.order_view import get_order_json
# 注文情報を取得する
# 例 https://127.0.0.1:8000/today/order_json?days_ago=-5
@shop_router.get("/me/order_json",response_class=HTMLResponse, tags=["shops"]) 
@log_decorator
async def order_json(request: Request, days_ago: str = Query(None)):

        return await get_order_json(request, days_ago)
'''
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="order_json()")

        # 注文追加
        user = await select_user(cookies['sub'])

        if user is None:
            logger.debug(f"user:{user} 取得に失敗しました")
            raise CustomException(
                status.HTTP_400_BAD_REQUEST,
                "order_json()",
                "select_user よりユーザー情報が取得できませんでした。")
            #return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        if days_ago is not None:
            logger.debug(f"days_ago: {int(days_ago)}")

        logger.debug(f"days_ago: {days_ago}")
        # 履歴取得
        if days_ago is None:
            logger.debug("全履歴を取得する") 
            orders = await select_shop_order(user.shop_name)
        elif days_ago.isdigit() or (days_ago.startswith('-') and days_ago[1:].isdigit()):
            logger.debug(f"{days_ago} 日前までの履歴を取得する")
            orders = await select_shop_order(user.shop_name, days_ago)
        else:
            raise CustomException(
                status.HTTP_400_BAD_REQUEST,
                "order_json()",
                "days_ago の値が無効です")
            #return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

        if not orders:
            #raise CustomException(status.HTTP_400_BAD_REQUEST, "len(orders)=0 注文が見つかりません。")
            logger.debug("No orders found or error occurred.")
            return JSONResponse({"message": "注文が見つかりません。"}, status_code=status.HTTP_204_NO_CONTENT)

        # 日時で逆順
        orders.sort(key=lambda x: x.created_at, reverse=True)

        #print("ここまできた 3")
        for order in orders:
        #    print(order.model_dump_json())
            logger.debug(f"orders: {order.model_dump_json()}")

        #print("ここまできた 4")
 
        orders_dict = [order.model_dump() for order in orders]
        orders_json = json.dumps(orders_dict, default=str)  # ← datetime を文字列に変換

        return JSONResponse(content=json.loads(orders_json))  # JSON をパースしてレスポンス

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"/order_json()",
            f"Error: {str(e)}")
'''