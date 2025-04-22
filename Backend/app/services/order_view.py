# services/order_view.py
'''
    1. order_table_view(request: Request, response: Response):
        orderリストを降順にソートし、チェックされた件数をカウント。
        company_nameごとに注文件数を集計。
        ２件以上の注文がある会社のみを抽出。
        テンプレートをレンダリングして返す。
    2. get_order_json(request: Request, days_ago: str = Query(None)):
        ユーザー情報を取得し、days_agoの値を検証。
        履歴を取得してJSON形式で返す。
    3. batch_update_orders(updates: list[dict]):
        注文のキャンセル状態を更新する。
        SQL文を実行して、変更をコミット。
        エラーが発生した場合はログに記録。
'''
from venv import logger
from fastapi import HTTPException, APIRouter, Query, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from utils.utils import log_decorator, get_all_cookies
from utils.exception import CustomException

templates = Jinja2Templates(directory="templates")

view_router = APIRouter()

from models.order import select_orders_by_shop_ago
from models.user import select_user
from database.local_postgresql_database import AsyncSessionLocal


from collections import Counter

# 注文一覧テーブル表示
@log_decorator
async def order_table_view(
                response: Response,
                orders ,
                redirect_url: str,
                context: dict):

    try:
        # ordersリストをin-placeで降順にソート
        orders.sort(key=lambda x: x.order_id, reverse=True)

        # チェックが入っている注文の件数をカウント（order.canceled が True の場合）
        checked_count = sum(1 for order in orders if order.canceled)

        # company_nameごとに注文件数を集計
        company_counts = Counter(order.company_name for order in orders)

        # ※全件数を集計したい場合は、以下のようにフィルタを外します
        aggregated_orders = [[company, count] for company, count in company_counts.items()]
        # ２件以上の注文がある会社のみを抽出
        # aggregated_orders = [[company, count] for company, count in company_counts.items() if count >= 2]

        logger.debug(f"orders.model_dump(): {orders[0].model_dump()=}")



        calculated_orders_context = {        
            'checked_count': checked_count,
            'aggregated_orders': aggregated_orders,
        }

        context.update(calculated_orders_context)

        templates.TemplateResponse("order_table.html", context)

        template_response = templates.TemplateResponse(
            redirect_url, context)
        # 必須！　Set-CookieヘッダーがNoneでないことを確認
        set_cookie_header = response.headers.get("Set-Cookie")
        if set_cookie_header:
            template_response.headers["Set-Cookie"] = set_cookie_header

        return template_response

    except HTTPException as e:
        raise HTTPException(e.status_code, e.detail)
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/order_table_view()",
            f"Error: {str(e)}")


import json

@log_decorator
async def get_order_json(request: Request, days_ago: str = Query(None)):
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        user = await select_user(cookies['sub'])
        if user is None:
            logger.debug(f"user:{user=} 取得に失敗しました")
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        # --- ✅ days_ago のバリデーション ---
        if days_ago is None or days_ago.strip() == "":
            logger.debug("days_ago の値が無効です（None または 空文字）")
            return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

        try:
            days_ago_int = int(days_ago)
        except ValueError:
            logger.debug("days_ago の値が数値でないため無効です")
            return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

        logger.debug(f"---days_ago: {days_ago_int=}")
        # -----------------------------------

        # 履歴取得処理（days_ago_intを使って履歴を取得）
        orders = await select_orders_by_shop_ago(user.shop_name, days_ago_int)
        print(f"orders.len(): {len(orders)}")
        if not orders:
            logger.info("No orders found or error occurred.")
            return JSONResponse({"message": "注文が見つかりません。"}, status_code=404)

        # 日時で逆順にソート
        orders.sort(key=lambda x: x.created_at, reverse=True)

        orders_dict = [order.model_dump() for order in orders]
        orders_json = json.dumps(orders_dict, default=str)

        return JSONResponse(content=json.loads(orders_json), media_type="application/json; charset=utf-8")

    except Exception as e:
        logger.warning(f"get_order_json Error: {str(e)=}")
        return JSONResponse({"error": f"エラーが発生しました: {str(e)}"}, status_code=500)


# from sqlalchemy import text
# from schemas.order_schemas import OrderUpdateList
from sqlalchemy import update
from models.order import Order  # OrdersはSQLAlchemyのモデル定義を想定

@log_decorator
async def batch_update_orders(updates: list[dict]):
    """
    DB更新の実処理。キャンセルチェック状態をバッチで更新します。
    SQLAlchemyのORM updateを使用して各注文を更新します。
    """
    try:
        async with AsyncSessionLocal() as session:
            for update_data in updates:
                stmt = (
                    update(Order)
                    .where(Order.order_id == update_data["order_id"])
                    .values(canceled=update_data["canceled"])
                )
                await session.execute(stmt)
            await session.commit()

        return {"message": "Orders updated successfully"}

    except Exception as e:
        logger.error(f"batch_update_orders Error: {str(e)}")
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "batch_update_orders()",
            f"予期せぬエラー: {str(e)=}"
        )


