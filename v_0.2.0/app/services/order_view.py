# order_view.py
from collections import Counter
import json
from venv import logger
from fastapi import HTTPException, APIRouter, Query, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from database.sqlite_database import get_connection, select_shop_order, select_user
from database.sqlite_database import CustomException
from utils.utils import log_decorator, get_all_cookies

templates = Jinja2Templates(directory="templates")

view_router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

# 注文一覧テーブル表示
@log_decorator
#async def order_table_view(request: Request, response: Response, orders, order_details , redirect_url: str):
async def order_table_view(request: Request, response: Response, orders , redirect_url: str):

    try:
        # ordersリストをin-placeで降順にソート
        orders.sort(key=lambda x: x.order_id, reverse=True)

        # チェックが入っている注文の件数をカウント（order.canceled が True の場合）
        checked_count = sum(1 for order in orders if order.canceled)

        # company_nameごとに注文件数を集計
        company_counts = Counter(order.company_name for order in orders)
        # ２件以上の注文がある会社のみを抽出
        # aggregated_orders = [[company, count] for company, count in company_counts.items() if count >= 2]
        # ※全件数を集計したい場合は、以下のようにフィルタを外します
        aggregated_orders = [[company, count] for company, count in company_counts.items()]


        print(f"orders.model_dump(): {orders[0].model_dump()}")
        # コンテキストに集計結果も追加
        context = {
            'request': request,
            'orders': orders,
            'order_count': len(orders),
            'checked_count': checked_count,
            'aggregated_orders': aggregated_orders,
            "base_url": "https://192.168.3.19:8000",
            "order_details": orders[0].model_dump() if orders else None
        }

        templates.TemplateResponse("order_table.html", context)
        #print("ここまできた 2")
        template_response = templates.TemplateResponse(
            redirect_url, context)
        #print("ここまできた 3")
        # 必須！　Set-CookieヘッダーがNoneでないことを確認
        set_cookie_header = response.headers.get("Set-Cookie")
        #print("ここまできた 4")
        if set_cookie_header:
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

@log_decorator
async def get_order_json(request: Request, days_ago: str = Query(None)):
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        user = await select_user(cookies['sub'])
        if user is None:
            logger.debug(f"user:{user} 取得に失敗しました")
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        # days_ago の値が None、空文字、または数値形式でなければエラーを返す
        #if days_ago is None or days_ago.strip() == "":
        if days_ago.__len__ == 0:
            logger.debug("days_ago の値が無効です (空文字または未指定)")
            return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)
        if not (days_ago.isdigit() or (days_ago.startswith('-') and days_ago[1:].isdigit())):
            logger.debug("days_ago の値が無効です (半角数値以外)")
            return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

        # 正常な場合は整数に変換
        days_ago_int = int(days_ago)
        logger.debug(f"days_ago: {days_ago_int}")

        # 履歴取得処理（days_ago_intを使って履歴を取得）
        orders = await select_shop_order(user.shop_name, days_ago_int)

        if not orders:
            logger.info("No orders found or error occurred.")
            return JSONResponse({"message": "注文が見つかりません。"}, status_code=404)

        # 日時で逆順にソート
        orders.sort(key=lambda x: x.created_at, reverse=True)

        orders_dict = [order.model_dump() for order in orders]
        orders_json = json.dumps(orders_dict, default=str)

        return JSONResponse(content=json.loads(orders_json), media_type="application/json; charset=utf-8")

    except Exception as e:
        logger.warning(f"/order_json Error: {str(e)}")
        return JSONResponse({"error": f"エラーが発生しました: {str(e)}"}, status_code=500)


# キャンセルチェック状態を更新
async def batch_update_orders(updates: list[dict]):
    try:
        values = [(change["canceled"], change["order_id"]) for change in updates]
        sql = "UPDATE orders SET canceled = ? WHERE order_id = ?"

        conn = await get_connection()  # ✅ 非同期DB接続
        try:
            cur = await conn.cursor()  # ✅ `async with` は不要
            await cur.executemany(sql, values)  # ✅ `await` なし
            await conn.commit()  # ✅ コミットを実行
        finally:
            await conn.close()  # ✅ 明示的にクローズ

        return {"message": "Orders updated successfully"}

    except Exception as e:
        logger.error(f"batch_update_orders Error: {str(e)}")
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "batch_update_orders()",
            f"予期せぬエラー: {str(e)}")

