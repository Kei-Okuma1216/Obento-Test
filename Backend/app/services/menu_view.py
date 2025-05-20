# menu_view.py
import json
from typing import Optional
from venv import logger
from fastapi import HTTPException, APIRouter, Query, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from database.local_postgresql_database import get_connection, select_shop_order, select_user
from utils.utils import log_decorator, check_permission, get_all_cookies

templates = Jinja2Templates(directory="templates")

view_router = APIRouter()

# メニュー一覧カード表示
@log_decorator
async def menu_cards_view(request: Request, response: Response,
                          menus: Optional[dict], redirect_url: str):
    try:
        if await check_permission(request, [1, 2, 10, 99]) == False:
            return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})

        #print("ここまできた 1")
        context = {'request': request, 'menus': menus}
        inner_table = "cards.html"

        templates.TemplateResponse(inner_table, context)
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
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"/menu_cards_view()",
            f"Error: {str(e)}")

@log_decorator
async def get_menu_json(request: Request, shop_id: str = Query(None)):
    try:
        if await check_permission(request, [1, 2, 10, 99]) == False:
            return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})
        
        cookies = get_all_cookies(request)
        if not cookies:
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        user = await select_user(cookies['sub'])
        if user is None:
            logger.debug(f"user:{user} 取得に失敗しました")
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        # shop_id の値が None、空文字、または数値形式でなければエラーを返す
        #if days_ago is None or days_ago.strip() == "":
        if shop_id.__len__ == 0:
            logger.debug("shop_id の値が無効です (空文字または未指定)")
            return JSONResponse({"error": "shop_id の値が無効です"}, status_code=400)

        # 正常な場合は整数に変換
        shop_id_int = int(shop_id)
        logger.debug(f"shop_id: {shop_id_int}")

        # 履歴取得処理（days_ago_intを使って履歴を取得）
        orders = await select_shop_order(user.shop_name, shop_id)

        if not orders:
            logger.info("No orders found or error occurred.")
            return JSONResponse({"message": "注文が見つかりません。"}, status_code=404)

        # 日時で逆順にソート
        orders.sort(key=lambda x: x.created_at, reverse=True)

        orders_dict = [order.model_dump() for order in orders]
        # orders_json = json.dumps(orders_dict, default=str)
        orders_json = [json.loads(order.model_dump_json()) for order in orders]


        return JSONResponse(content=json.loads(orders_json), media_type="application/json; charset=utf-8")

    except Exception as e:
        logger.warning(f"/order_json Error: {str(e)}")
        return JSONResponse({"error": f"エラーが発生しました: {str(e)}"}, status_code=500)


# キャンセルチェック状態を更新
async def batch_update_orders(updates: list[dict]):
    try:
        values = [(change["checked"], change["order_id"]) for change in updates]
        sql = "UPDATE Orders SET checked = ? WHERE order_id = ?"

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
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "batch_update_orders()",
            f"予期せぬエラー: {str(e)}")

