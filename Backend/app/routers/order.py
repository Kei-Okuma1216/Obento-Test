# routers/order.py
# 注文一覧API
'''
    1. get_orders_by_user(user_id: int, begin: str = None, end: str = None):
    2. get_orders_by_manager_company(user_id: int, company_id: int, begin: str = None, end: str = None):
    3. get_orders_by_shop(shop_name: str, target_date: str):
    4. get_orders_range_by_shop(shop_id: int, begin: str = None, end: str = None):
    5. get_orders_by_admin(shop_name: str, target_date: str):
    6. get_orders_range_by_admin(begin: str = None, end: str = None):
    7. get_order_range(user_id=None, company_id=None, shop_id=None, is_admin=False, begin=None, end=None):

    8. get_order_summary_by_user(user_id: int):
    9. get_order_summary_by_manager_company(user_id: int, company_id: int):
    10. get_order_summary_by_shop(shop_id: int):
    11. get_order_summary_by_admin():
    12. get_order_summary(user_id=None, company_id=None, shop_id=None, is_admin=False):

'''
from fastapi import APIRouter


order_api_router = APIRouter(
    prefix="/api/v1/orders",
    tags=["order"]
    )

from log_unified import logger

# 1. 一般ユーザー注文一覧
@order_api_router.get("/user/{user_id}")
async def get_orders_by_user(user_id: int, begin: str = None, end: str = None):
    return await get_order_range(user_id=user_id, begin=begin, end=end)

# 2. 契約企業ユーザー注文一覧
@order_api_router.get("/manager/{user_id}/company/{company_id}")
async def get_orders_by_manager_company(user_id: int, company_id: int, begin: str = None, end: str = None):
    return await get_order_range(user_id=user_id, company_id=company_id, begin=begin, end=end)

# 3. 店舗ユーザー注文一覧
@order_api_router.get("/shop/{shop_id}")
async def get_orders_range_by_shop(shop_id: int, begin: str = None, end: str = None):
    return await get_order_range(shop_id=shop_id, begin=begin, end=end)

# 4. 管理者ユーザー注文一覧
@order_api_router.get("/admin")
async def get_orders_range_by_admin(begin: str = None, end: str = None):
    return await get_order_range(is_admin=True, begin=begin, end=end)



from datetime import datetime

# 5. 共通：パラメータによる注文一覧取得
async def get_order_range(user_id=None, company_id=None, shop_id=None, is_admin=False, begin=None, end=None):
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
        from models.user import select_user_by_id
        from models.order import select_orders_by_user_at_date_range

        user = await select_user_by_id(user_id)  # user_id → username 変換
        if not user:
            print(f"if not user:{user}")
            return {"orders": []}

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



# 6. 注文概要API 設計（FAX送信用）

# 1. 一般ユーザーの注文概要
@order_api_router.get("/user/{user_id}/summary")
async def get_order_summary_by_user(user_id: int):
    return await get_order_summary(user_id=user_id)

# 2. 契約企業ユーザーの注文概要
@order_api_router.get("/manager/{user_id}/company/{company_id}/summary")
async def get_order_summary_by_manager_company(user_id: int, company_id: int):
    return await get_order_summary(user_id=user_id, company_id=company_id)

# 3. 店舗ユーザーの注文概要
@order_api_router.get("/shop/{shop_id}/summary")
async def get_order_summary_by_shop(shop_id: int):
    return await get_order_summary(shop_id=shop_id)

# 4. 管理者の注文概要
@order_api_router.get("/admin/summary")
async def get_order_summary_by_admin():
    return await get_order_summary(is_admin=True)

# 5. 共通処理
from models.order import select_order_summary
import datetime

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


from fastapi.responses import JSONResponse
from models.order import select_orders_by_admin_at_date
from datetime import datetime
import json
        
# 注文ログファイルの内容JSONを表示するエンドポイント
@order_api_router.get("/orders/admin", tags=["admin"])
async def get_admin_orders(target_date: str):
    """
    管理者用 注文JSON取得API
    パラメータ target_date は yyyy-mm-dd 形式の日付文字列
    """
    try:
        if not target_date or target_date.lower() in ["", "null", "none"]:
            return JSONResponse({"error": "開始日が指定されていません"}, status_code=400)

        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            return JSONResponse({"error": "開始日フォーマットが不正です (yyyy-mm-dd 形式)"}, status_code=400)

        # 管理者用の注文取得関数を呼び出し
        orders = await select_orders_by_admin_at_date(target_date)

        if not orders:
            return JSONResponse({"message": "注文が見つかりません"}, status_code=404)

        # Pydanticモデルから辞書リストに変換
        # orders_json = [order.model_dump() for order in orders]
        orders_json = [json.loads(order.model_dump_json()) for order in orders]


        return JSONResponse(content=orders_json, media_type="application/json; charset=utf-8")

    except Exception as e:
        logger.exception("注文取得API実行中にサーバーエラー発生")
        return JSONResponse({"error": f"サーバーエラー: {str(e)}"}, status_code=500)



from models.order import select_orders_by_shop_at_date

@order_api_router.get("/shop", tags=["shops"])
async def get_orders_by_shop(shop_name: str, target_date: str):
    """
    店舗用 注文JSON取得API
    パラメータ:
      - shop_name: 店舗名 (例: shop01)
      - target_date: yyyy-mm-dd 形式の日付文字列
    """
    try:
        if not target_date or target_date.lower() in ["", "null", "none"]:
            return JSONResponse({"error": "開始日が指定されていません"}, status_code=400)

        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            return JSONResponse({"error": "開始日フォーマットが不正です (yyyy-mm-dd 形式)"}, status_code=400)

        # 店舗用の注文取得関数を呼び出し
        orders = await select_orders_by_shop_at_date(shop_name, target_date)

        # if not orders:
            # return JSONResponse({"message": "注文が見つかりません"}, status_code=404)
        if not orders:
            return JSONResponse([], media_type="application/json; charset=utf-8")

        # Pydanticモデルから辞書リストに変換
        # orders_json = [order.model_dump() for order in orders]
        orders_json = [json.loads(order.model_dump_json()) for order in orders]
        
        return JSONResponse(content=orders_json, media_type="application/json; charset=utf-8")

    except Exception as e:
        logger.exception("注文取得API実行中にサーバーエラー発生")
        return JSONResponse({"error": f"サーバーエラー: {str(e)}"}, status_code=500)
