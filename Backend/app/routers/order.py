# routers/order.py
# 注文一覧API
'''
    1. 
    2. 


'''
from fastapi import APIRouter

# order_api_router = APIRouter(
#     tags=["order"]
# )
order_api_router = APIRouter(
    prefix="/api/v1/orders",
    tags=["order"]
    )


# 1. 一般ユーザー注文一覧
@order_api_router.get("/user/{user_id}")
async def get_user_orders(user_id: int, begin: str = None, end: str = None):
    return await get_order_list_range(user_id=user_id, begin=begin, end=end)

# 2. 契約企業ユーザー注文一覧
@order_api_router.get("/manager/{user_id}/company/{company_id}")
async def get_manager_company_orders(user_id: int, company_id: int, begin: str = None, end: str = None):
    return await get_order_list_range(user_id=user_id, company_id=company_id, begin=begin, end=end)

# 3. 店舗ユーザー注文一覧
@order_api_router.get("/shop/{shop_id}")
async def get_shop_orders(shop_id: int, begin: str = None, end: str = None):
    return await get_order_list_range(shop_id=shop_id, begin=begin, end=end)

# 4. 管理者ユーザー注文一覧
@order_api_router.get("/admin")
async def get_admin_orders(begin: str = None, end: str = None):
    return await get_order_list_range(is_admin=True, begin=begin, end=end)


# 5. パラメータによる注文一覧取得
from datetime import datetime

async def get_order_list_range(user_id=None, company_id=None, shop_id=None, is_admin=False, begin=None, end=None):
    import datetime
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")

    # デフォルト値設定
    end_date_str = end or today_str # もしif end <> end_str: の場合は、何かする必要がある。いまはおかしい。
    begin_date_str = begin or today_str

    # 検索期間ログ出力
    print(f"[DEBUG] 検索期間: begin={begin_date_str}, end={end_date_str}")

    # 日付計算
    try:
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        begin_date = datetime.datetime.strptime(begin_date_str, "%Y-%m-%d").date()
        days_ago = (end_date - begin_date).days
    except ValueError:
        raise ValueError("日付形式は 'YYYY-MM-DD' で指定してください")

    # 分岐実行
    if is_admin:
        from models.order import select_orders_ago
        orders = await select_orders_ago(days_ago)

    elif user_id and not company_id and not shop_id:
        from models.order import select_orders_by_user_ago
        orders = await select_orders_by_user_ago(user_id, days_ago)

    elif user_id and company_id and not shop_id:
        from models.order import select_orders_by_company_ago
        orders = await select_orders_by_company_ago(user_id, company_id, days_ago)

    elif shop_id:
        from models.order import select_orders_by_shop_ago
        orders = await select_orders_by_shop_ago(shop_id, days_ago)

    else:
        orders = []

    # モデルを辞書に変換
    order_dicts = [order.model_dump() for order in orders] if orders else []

    return {"orders": order_dicts}



# 6. 注文概要API 設計（FAX送信用）

# 1. 一般ユーザーの注文概要
@order_api_router.get("/user/{user_id}/summary")
async def get_user_order_summary(user_id: int):
    return await get_order_summary(user_id=user_id)

# 2. 契約企業ユーザーの注文概要
@order_api_router.get("/manager/{user_id}/company/{company_id}/summary")
async def get_manager_company_order_summary(user_id: int, company_id: int):
    return await get_order_summary(user_id=user_id, company_id=company_id)

# 3. 店舗ユーザーの注文概要
@order_api_router.get("/shop/{shop_id}/summary")
async def get_shop_order_summary(shop_id: int):
    return await get_order_summary(shop_id=shop_id)

# 4. 管理者の注文概要
@order_api_router.get("/admin/summary")
async def get_admin_order_summary():
    return await get_order_summary(is_admin=True)

# 5. 共通処理
async def get_order_summary(user_id=None, company_id=None, shop_id=None, is_admin=False):
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

