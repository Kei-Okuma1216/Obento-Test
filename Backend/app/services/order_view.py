# services/order_view.py
'''
    1. order_table_view(request: Request, response: Response):
    2. get_order_json(request: Request, days_ago: str = Query(None)):
    3. batch_update_orders(updates: list[dict]):
'''
from fastapi import HTTPException, APIRouter, Query, Request, Response, status
from utils.utils import log_decorator, get_all_cookies
from utils.helper import redirect_login_failure

view_router = APIRouter()

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

from venv import logger

from collections import Counter

# 注文一覧テーブル表示
@log_decorator
async def order_table_view(request: Request, response: Response, orders, redirect_url: str, context: dict):
    try:
        # デバッグ出力追加
        # req_in_context = context.get("request", None)
        # print(f"context['request']: {req_in_context}")
        # print(f"type(context['request']): {type(req_in_context)}")

        # ordersリストをin-placeで降順にソート
        orders.sort(key=lambda x: x.order_id, reverse=True)

        # チェック済み注文の件数をカウント
        checked_count = sum(1 for order in orders if order.checked)

        # 会社別注文件数を集計
        company_counts = Counter(order.company_name for order in orders)
        aggregated_orders = [[company, count] for company, count in company_counts.items()]

        # logger.debug(f"orders.model_dump(): {orders[0].model_dump()=}")
        if orders:
            logger.debug(f"orders.model_dump(): {orders[0].model_dump()=}")
        else:
            logger.debug("orders is empty")

        # ここで username をコンテキストに追加（shop_idやmanager_idを使う）
        # current_username = context.get("shop_id") or context.get("manager_id") or "unknown"

        # ★ ここから追加修正
        if 'username' not in context:
            current_username = context.get("shop_id") or context.get("manager_id") or "unknown"
            context.update({'username': current_username})
        # ★ ここまで追加修正

        # コンテキスト更新
        context.update({
            'checked_count': checked_count,
            'aggregated_orders': aggregated_orders,
            # 'username': current_username  # ★ ここに追加
        })
        context["request"] = request
        
        # テンプレート応答作成
        template_response = templates.TemplateResponse(redirect_url, context)

        # Set-Cookie ヘッダー引き継ぎ
        set_cookie_header = response.headers.get("Set-Cookie")
        if set_cookie_header:
            template_response.headers["Set-Cookie"] = set_cookie_header

        return template_response

    except HTTPException as e:
        logger.exception(f"HTTPException: {e.detail}")
        return redirect_login_failure(request, "不正なアクセス、またはセッションが切れました。")
    except Exception as e:
        logger.exception("shop_view で予期せぬエラーが発生")
    
        return redirect_login_failure(request, "システムエラーが発生しました。管理者にお問い合わせください。")



import json
from fastapi.responses import JSONResponse
from models.order import select_orders_by_shop_ago
from models.user import select_user
from database.local_postgresql_database import AsyncSessionLocal

@log_decorator
async def get_order_json(request: Request, days_ago: str = Query(None), shop_code: str = None):
    try:
        # shop_code が指定されていればそれを使う（管理者・店舗ユーザーからのアクセス想定）
        if shop_code:
            shop_name = shop_code
        else:
            # 通常のログインユーザーから取得
            cookies = get_all_cookies(request)
            if not cookies:
                return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

            user = await select_user(cookies['sub'])
            if user is None:
                logger.debug(f"user:{user=} 取得に失敗しました")
                return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

            shop_name = user.shop_name

        # --- ✅ days_ago のバリデーション ---
        if days_ago is None or days_ago.strip() == "":
            logger.debug("days_ago の値が無効です（None または 空文字）")
            return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

        try:
            days_ago_int = int(days_ago)
        except ValueError:
            logger.debug("days_ago の値が数値でないため無効です")
            return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)
        else:
            logger.debug(f"---days_ago: {days_ago_int=}")
        # -----------------------------------

        # 履歴取得処理
        orders = await select_orders_by_shop_ago(shop_name, days_ago_int)

        if not orders:
            logger.info("No orders found.")
            return JSONResponse({"message": "注文が見つかりません。"}, status_code=404)

        orders.sort(key=lambda x: x.created_at, reverse=True)
        orders_json = [json.loads(order.model_dump_json()) for order in orders]

    except Exception as e:
        logger.warning(f"get_order_json Error: {str(e)=}")
        return JSONResponse({"error": f"エラーが発生しました: {str(e)}"}, status_code=500)
    else:
        return JSONResponse(content=orders_json, media_type="application/json; charset=utf-8")

# @log_decorator
# async def get_order_json(request: Request, days_ago: str = Query(None)):
#     try:
#         cookies = get_all_cookies(request)
#         if not cookies:
#             return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

#         user = await select_user(cookies['sub'])
#         if user is None:
#             logger.debug(f"user:{user=} 取得に失敗しました")
#             return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

#         # --- ✅ days_ago のバリデーション ---
#         if days_ago is None or days_ago.strip() == "":
#             logger.debug("days_ago の値が無効です（None または 空文字）")
#             return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

#         try:
#             days_ago_int = int(days_ago)
#         except ValueError:
#             logger.debug("days_ago の値が数値でないため無効です")
#             return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)
#         else:
#             logger.debug(f"---days_ago: {days_ago_int=}")
#         # -----------------------------------

#         # 履歴取得処理（days_ago_intを使って履歴を取得）
#         orders = await select_orders_by_shop_ago(user.shop_name, days_ago_int)

#         print(f"orders.len(): {len(orders) if orders else '注文は0件です'}")
#         if not orders:
#             logger.info("No orders found.")  # エラーではないため wording 修正
#             # logger.info("No orders found or error occurred.")
#             return JSONResponse({"message": "注文が見つかりません。"}, status_code=404)

#         # 日時で逆順にソート
#         orders.sort(key=lambda x: x.created_at, reverse=True)

#         # orders_dict = [order.model_dump() for order in orders]
#         # orders_json = json.dumps(orders_dict, default=str)
#         orders_json = [json.loads(order.model_dump_json()) for order in orders]

#     except Exception as e:
#         logger.warning(f"get_order_json Error: {str(e)=}")
#         return JSONResponse({"error": f"エラーが発生しました: {str(e)}"}, status_code=500)
#     else:
#         # return JSONResponse(content=json.loads(orders_json), media_type="application/json; charset=utf-8")
#         return JSONResponse(content=orders_json, media_type="application/json; charset=utf-8")

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from models.order import Order
from fastapi import HTTPException, status

@log_decorator
async def batch_update_orders(updates: list[dict]):
    """
    複数の注文キャンセル状態を一括更新。
    失敗した注文も記録しつつ、処理を継続します。
    """
    failed_updates = []

    try:
        async with AsyncSessionLocal() as session:
            for update_data in updates:
                stmt = (
                    update(Order)
                    .where(Order.order_id == update_data["order_id"])
                    .values(checked=update_data["checked"])
                )
                try:
                    await session.execute(stmt)

                except (IntegrityError, OperationalError, SQLAlchemyError) as db_err:
                    logger.exception(f"注文ID {update_data['order_id']} の更新失敗: {db_err}")
                    failed_updates.append(update_data['order_id'])
                except Exception as ex:
                    logger.exception(f"注文ID {update_data['order_id']} で予期せぬエラー: {ex}")
                    failed_updates.append(update_data['order_id'])

            try:
                await session.commit()
            except Exception as commit_err:
                await session.rollback()
                logger.exception(f"コミット失敗: {commit_err}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"コミット処理中にエラーが発生しました: {str(commit_err)}"
                )

        if failed_updates:
            logger.warning(f"一部注文の更新に失敗しました: {failed_updates}")
            return {"message": "一部注文の更新に失敗しました", "failed_order_ids": failed_updates}

    except Exception as e:
        logger.exception(f"batch_update_orders 全体失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"サーバー内部エラーが発生しました: {str(e)}"
        )
    else:
        return {"message": "すべての注文を正常に更新しました"}



