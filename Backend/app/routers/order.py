# routers/order.py
# 注文一覧API
'''
    # 注文一覧（日付指定）
     1. get_orders_date_by_admin(target_date: date):
     2. get_orders_date_by_shop(shop_name: str, target_date: str):
     3. get_orders_date_by_manager_company_date(user_id: int, company_id: int, begin: str = None, end: str = None):
     4. get_orders_date_by_username(username: str, target_date: date):
    # 注文一覧（日付範囲で取得）
     5. get_orders_range_by_admin(begin: str = None, end: str = None):
     6. get_orders_range_by_shop(shop_id: int, begin: str = None, end: str = None):
     7. get_orders_range_by_manager_company(
     8. get_orders_range_by_user(user_id: int, begin: date, end: date):
     9. get_order_range_common(user_id=None, company_id=None, shop_id=None, is_admin=False, begin=None, end=None):
    # 注文概要（FAX送信用）
    10. get_orders_summary_by_user(user_id: int):
    11. get_orders_summary_by_manager_company(user_id: int, company_id: int):
    12. get_orders_summary_by_shop(shop_id: int):
    13. get_orders_summary_by_admin():
    14. get_orders_summary_common(user_id=None, company_id=None, shop_id=None, is_admin=False):
    # 注文キャンセル
    15. set_order_cancel_by_user(payload: CancelOrderRequest):

'''
from fastapi import APIRouter


order_api_router = APIRouter(
    prefix="/api/v1/order",
    tags=["order"]
    )

from log_unified import logger
from fastapi import Query
from datetime import date
from typing import List
from schemas.order_schemas import OrderModel

'''-------------------------------------------------------------------'''
# 注文一覧（日付指定）
from fastapi import Query, HTTPException
from datetime import date
from typing import List
from schemas.order_schemas import OrderModel  # ← Pydanticモデル
from models.order import (
    select_orders_by_admin_at_date,
    select_orders_by_shop_at_date
)

# 1. 管理者ユーザー
@order_api_router.get(
    "/admin/orders",
    summary="注文一覧取得（指定日）：管理者ユーザー",
    description="指定した日付の全注文一覧を取得します（管理者専用）。",
    response_model=List[OrderModel],
    tags=["order: single"]
)
async def get_orders_date_by_admin(
    target_date: date = Query(..., description="注文日（YYYY-MM-DD形式）")
):
    try:
        orders = await select_orders_by_admin_at_date(target_date)
    except Exception as e:
        logger.exception("注文取得中にサーバーエラー")
        raise HTTPException(status_code=500, detail="注文の取得に失敗しました")

    if not orders:
        raise HTTPException(status_code=404, detail="注文が見つかりません")

    return orders


from models.order import select_orders_by_shop_at_date
# 2. 店舗ユーザー
@order_api_router.get(
    "/shop/orders",
    summary="注文一覧取得（指定日）：店舗ユーザー",
    description="指定した店舗名と日付に該当する注文一覧を取得します。",
    response_model=List[OrderModel],
    tags=["order: single"]
)
async def get_orders_date_by_shop(
    shop_name: str = Query(..., description="店舗名（例: shop01）"),
    target_date: date = Query(..., description="注文日（YYYY-MM-DD形式）")
):
    try:
        orders = await select_orders_by_shop_at_date(shop_name, target_date)
    except Exception as e:
        logger.exception("注文取得中にサーバーエラーが発生しました")
        raise HTTPException(status_code=500, detail="注文の取得中にエラーが発生しました")

    # 注文がない場合でも FastAPI は空リストを 200 OK で返す
    return orders


from models.order import select_orders_by_company_at_date
# 3. 契約企業ユーザー
@order_api_router.get(
    "/manager/{company_id}/orders",
    summary="注文一覧取得（指定日）：契約企業ユーザー",
    description="指定された企業IDと注文日から、契約企業の注文一覧を取得します。",
    response_model=List[OrderModel],
    tags=["order: single"]
)
async def get_orders_date_by_manager_company_date(
    company_id: int,
    target_date: date = Query(..., description="注文日（YYYY-MM-DD形式）")
):
    try:
        orders = await select_orders_by_company_at_date(company_id, target_date)
    except Exception as e:
        logger.exception("契約企業の注文取得中にサーバーエラーが発生しました")
        raise HTTPException(status_code=500, detail="注文の取得中にエラーが発生しました")

    return orders  # 空リストも200で返却（自然なREST挙動）


from models.order import select_orders_by_user_at_date
# 4. 一般ユーザー
# 注意：ここは{user_id}に書き直す必要がある。
@order_api_router.get(
    "/user/{username}/orders",
    summary="注文一覧取得（指定日）：一般ユーザー",
    description="指定されたユーザー名と注文日から、該当ユーザーの注文一覧を取得します。",
    response_model=List[OrderModel],
    tags=["order: single"]
)
async def get_orders_date_by_username(
    username: str,
    target_date: date = Query(..., description="注文日（YYYY-MM-DD形式）")
):
    try:
        orders = await select_orders_by_user_at_date(username, target_date)
    except Exception as e:
        logger.exception("ユーザーの注文取得中にサーバーエラーが発生しました")
        raise HTTPException(status_code=500, detail="注文の取得中にエラーが発生しました")

    return orders

'''-------------------------------------------------------------------'''
# 注文一覧（日付範囲で取得） クエリオブジェクトで条件指定する
# schemas/order_schemas.py
from pydantic import BaseModel
from typing import List

class OrderListResponse(BaseModel):
    orders: List[OrderModel]

# 1. 管理者ユーザー
@order_api_router.get(
    "/admin/date_range/orders",
    summary="注文一覧取得（日付範囲）：管理者ユーザー",
    description="管理者が全体の注文一覧を取得します。日付範囲（begin, end）でフィルタリング可能です。",
    response_model=OrderListResponse,
    tags=["order: range"]
)
async def get_orders_range_by_admin(
    begin: date = Query(None, description="開始日（YYYY-MM-DD）"),
    end: date = Query(None, description="終了日（YYYY-MM-DD）")
):
    return await get_order_range_common(is_admin=True, begin=begin, end=end)

# 2. 店舗ユーザー
@order_api_router.get(
    "/shop/{shop_id}/date_range/orders",
    summary="注文一覧取得（日付範囲）：店舗ユーザー",
    description="指定された店舗IDの注文一覧を、日付範囲（begin, end）で取得します。",
    response_model=OrderListResponse,
    tags=["order: range"]
)
async def get_orders_range_by_shop(
    shop_id: int,
    begin: date = Query(None, description="開始日（YYYY-MM-DD）"),
    end: date = Query(None, description="終了日（YYYY-MM-DD）")
):
    return await get_order_range_common(shop_id=shop_id, begin=begin, end=end)

# 3. 契約企業ユーザー
@order_api_router.get(
    "/manager/{user_id}/company/{company_id}/date_range/orders",
    summary="注文一覧取得（日付範囲）：契約企業ユーザー",
    description="契約企業の担当者が、自社の注文一覧を取得します。日付範囲（begin, end）は任意です。",
    response_model=OrderListResponse,
    tags=["order: range"]
)
async def get_orders_range_by_manager_company(
    user_id: int,
    company_id: int,
    begin: date = Query(None, description="開始日（YYYY-MM-DD）"),
    end: date = Query(None, description="終了日（YYYY-MM-DD）")
):
    return await get_order_range_common(user_id=user_id, company_id=company_id, begin=begin, end=end)

# 4. 一般ユーザー
@order_api_router.get(
    "/user/{user_id}/date_range/orders",
    summary="注文一覧取得（日付範囲）：一般ユーザー",
    description="指定されたユーザーIDの注文一覧を、日付範囲で取得します（begin, end はオプション）",
    response_model=OrderListResponse,
    tags=["order: range"]
)
async def get_orders_range_by_user(
    user_id: int,
    begin: date = Query(None, description="開始日（YYYY-MM-DD）"),
    end: date = Query(None, description="終了日（YYYY-MM-DD）")
):
    return await get_order_range_common(user_id=user_id, begin=begin, end=end)


from datetime import datetime

# 5. 共通：パラメータによる注文一覧取得
async def get_order_range_common(user_id=None, company_id=None, shop_id=None, is_admin=False, begin=None, end=None):
    import datetime

    today = datetime.date.today()

    # begin の型チェックと変換
    if isinstance(begin, datetime.date):
        begin_date = begin
    elif isinstance(begin, str):
        begin_date = datetime.datetime.strptime(begin, "%Y-%m-%d").date()
    else:
        begin_date = today

    # end の型チェックと変換
    if isinstance(end, datetime.date):
        end_date = end
    elif isinstance(end, str):
        end_date = datetime.datetime.strptime(end, "%Y-%m-%d").date()
    else:
        end_date = today

    # 検索期間ログ出力
    print(f"[DEBUG] 検索期間: begin={begin_date}, end={end_date}")

    # 日数差を計算（shop や is_admin 用）
    days_ago = (end_date - begin_date).days
    print(f"{days_ago=}")
    # 実行分岐
    if is_admin:
        from models.order import select_orders_by_admin_at_date_range
        orders = await select_orders_by_admin_at_date_range(begin_date, end_date)


    elif user_id and not company_id and not shop_id:
        from models.user import select_user_by_id
        from models.order import select_orders_by_user_at_date_range

        user = await select_user_by_id(user_id)
        print(f"[DEBUG] username resolved to: {user.username}")
        if not user:
            print(f"if not user: {user}")
            return {"orders": []}

        print(user.username, begin_date, end_date)
        orders = await select_orders_by_user_at_date_range(user.username, begin_date, end_date)

    elif user_id and company_id and not shop_id:
        from models.order import select_orders_by_company_at_date_range
        orders = await select_orders_by_company_at_date_range(company_id, begin_date, end_date)

    elif shop_id:
        from models.order import select_orders_by_shop_ago
        orders = await select_orders_by_shop_ago(shop_id, days_ago)

    else:
        orders = []

    # モデルを辞書に変換
    order_dicts = [order.model_dump() for order in orders] if orders else []

    return {"orders": order_dicts}


'''-------------------------------------------------------------------'''
# 注文概要（FAX送信用）
from typing import Any, Dict
from schemas.order_schemas import BaseModel

class OrderSummaryResponse(BaseModel):
    summary: Dict[str, Any]  # または適切な構造がわかれば詳細に指定も可


# 1. 管理者ユーザー
@order_api_router.get(
    "/admin/summary",
    summary="注文概要取得：管理者ユーザー",
    description="管理者が全体の当日の注文概要を取得します。",
    response_model=OrderSummaryResponse,
    tags=["order: summary"]
)
async def get_orders_summary_by_admin():
    return await get_orders_summary_common(is_admin=True)

# 2. 店舗ユーザー
@order_api_router.get(
    "/shop/{shop_id}/summary",
    summary="注文概要取得：店舗ユーザー",
    description="指定された店舗の当日の注文概要を取得します。",
    response_model=OrderSummaryResponse,
    tags=["order: summary"]
)
async def get_orders_summary_by_shop(shop_id: int):
    return await get_orders_summary_common(shop_id=shop_id)


# 3. 契約企業ユーザー
@order_api_router.get(
    "/manager/{user_id}/company/{company_id}/summary",
    summary="注文概要取得：契約企業ユーザー",
    description="契約企業の担当者が、自社の注文概要（当日）を取得します。",
    response_model=OrderSummaryResponse,
    tags=["order: summary"]
)
async def get_orders_summary_by_manager_company(user_id: int, company_id: int):
    return await get_orders_summary_common(user_id=user_id, company_id=company_id)

# 4. 一般ユーザー
@order_api_router.get(
    "/user/{user_id}/summary",
    summary="注文概要取得：一般ユーザー",
    description="指定されたユーザーIDの当日の注文概要を取得します。",
    response_model=OrderSummaryResponse,
    tags=["order: summary"]
)
async def get_orders_summary_by_user(user_id: int):
    return await get_orders_summary_common(user_id=user_id)


# 5. 共通処理　注文概要
from models.order import select_order_summary
import datetime

async def get_orders_summary_common(user_id=None, company_id=None, shop_id=None, is_admin=False):
    today = datetime.date.today().strftime("%Y-%m-%d")
    conditions = {
        "user_id": user_id,
        "company_id": company_id,
        "shop_id": shop_id,
        "is_admin": is_admin,
        "begin_date": today,
        "end_date": today
    }
    summary_data = await select_order_summary(conditions)
    return {"summary": summary_data}

'''-------------------------------------------------------------------'''
# 注文キャンセル実行




# クライアントからのPOST例
# curl -X POST http://localhost:8000/api/v1/order/cancel \
#   -H "Content-Type: application/json" \
#   -d '{
#     "order_ids": [101, 102],
#     "user_id": 5
#   }'

# JavaScript Fetch APIの例
# fetch("/api/v1/order/cancel", {
#   method: "POST",
#   headers: {
#     "Content-Type": "application/json"
#   },
#   body: JSON.stringify({
#     order_ids: [101, 102],
#     user_id: 5
#   })
# });

from schemas.order_schemas import CancelOrderRequest
# class CancelOrderRequest(BaseModel):
#     order_ids: List[int]
#     user_id: int  # 必要なら。省略可能にしてもOK
from fastapi import HTTPException, Depends

from models.order import cancel_orders
from database.local_postgresql_database import get_db  # セッション取得用の依存関数
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import select_user_by_id 

@order_api_router.post(
    "/cancel",
    summary="注文キャンセルAPI",
    description="指定された注文IDの注文をキャンセルします。",
    tags=["order: cancel"]
)
async def set_order_cancel_by_user(
    payload: CancelOrderRequest,
    session: AsyncSession = Depends(get_db)
):
    try:
        # 引数の受け取り方
        # payload.order_ids → [101, 102]
        # payload.user_id   → 5
        user = await select_user_by_id(payload.user_id)
        if not user:
            raise HTTPException(404, "ユーザーが見つかりません")
        username = user.username
        
        print(f"[DEBUG] キャンセル対象の注文ID: {payload.order_ids}")
        result = await cancel_orders(payload.order_ids, username, session)

    except Exception as e:
        logger.exception("注文キャンセル中にエラーが発生しました")
        raise HTTPException(status_code=500, detail="注文キャンセルに失敗しました")

    if not result:
        raise HTTPException(status_code=404, detail="対象の注文が見つかりません")
    else:
        return {"message": "キャンセル処理が完了しました", "canceled_order_ids": result}
