# routers/router.py
'''
    1. get_admin_account(request: Request):
    2. get_account_or_404_response(username: str):
    3. get_manager_account(request: Request, user_id: int = Query(...)):
    4. get_shop_account(request: Request, user_id: str = Query(...)):
    5. get_account_by_id_or_404_response(user_id: int):

    6. get_holiday(date: str):
    7. get_delivery_date(date_str: str):
'''
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse

account_router = APIRouter(
    tags=["account"]
)


# 呼び方 お試しエンドポイント
# https://127.0.0.1:8000/api/items
@account_router.get(
    "/items/",
    include_in_schema=False,
    summary="表示テスト用エンドポイント",
    description="表示テストに使用する。お試しエンドポイント",
    tags=["account"]
)
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]



from schemas.user_schemas import UserResponse
from utils.helper import redirect_unauthorized
from utils.permission_helper import check_permission
from models.user import select_user



# 管理者アカウント情報の取得
@account_router.get(
    "/v1/account/admin",
    summary="アカウント情報の取得：管理者ユーザー",
    description="",
    response_model=UserResponse,
    tags=["account"]
)
async def get_admin_account(request: Request):

    if not await check_permission(request, [99]):
        return redirect_unauthorized(request, "管理者権限がありません。")

    return await get_account_or_404_response("admin")

async def get_account_or_404_response(username: str):
    """
    ユーザー取得&JSON返却を共通化。存在しない場合は404エラー。
    """
    user_info = await select_user(username)
    if user_info is None:
        raise HTTPException(status_code=404, detail=f"ユーザー {username} が見つかりません")
    print(f"{user_info=}")
    response_data = UserResponse(
        user_id=user_info.user_id,
        username=user_info.username,
        name=user_info.name,
        company_id=user_info.company_id,
        shop_name=user_info.shop_name,
        menu_id=user_info.menu_id,
        permission=user_info.permission
    )
    return JSONResponse(content=response_data.model_dump())


# 契約企業ユーザー情報の取得
@account_router.get(
    "/v1/account/manager",
    summary="アカウント情報の取得：契約企業ユーザー",
    description="",
    response_model=UserResponse,
    tags=["account"]
)
async def get_manager_account(request: Request, user_id: int = Query(...)):

    if not await check_permission(request, [2]):
        return redirect_unauthorized(request, "マネージャー権限がありません。")

    return await get_account_by_id_or_404_response(user_id)


# 店舗ユーザー情報の取得
@account_router.get(
    "/v1/account/shop",
    summary="アカウント情報の取得：店舗ユーザー",
    description="",
    response_model=UserResponse,
    tags=["account"]
)
async def get_shop_account(request: Request, user_id: str = Query(...)):

    if not await check_permission(request, [10]):
        return redirect_unauthorized(request, "店舗権限がありません。")

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効なユーザーID")

    return await get_account_by_id_or_404_response(user_id_int)


from models.user import select_user_by_id
# 共通
async def get_account_by_id_or_404_response(user_id: int):
    user_info = await select_user_by_id(user_id)  # user_id で検索
    if user_info is None:
        raise HTTPException(status_code=404, detail=f"ユーザーID {user_id} が見つかりません")
    # print(f"{user_info=}")
    response_data = UserResponse(
        user_id=user_info.user_id,
        username=user_info.username,
        name=user_info.name,
        company_id=user_info.company_id,
        shop_name=user_info.shop_name,
        menu_id=user_info.menu_id,
        permission=user_info.permission
    )
    return JSONResponse(content=response_data.model_dump())


'''--------------------------------------------------------------------------'''
from fastapi.responses import JSONResponse
from config.config_loader import load_holiday_map

@account_router.get(
    "/v1/check_holiday",
    summary="祝日名の取得：共通",
    description=f"指定された日付が祝日かどうかを判定し、祝日名を返すAPI 例: /api/check_holiday?date=2025/1/1",
    tags=["util"]
)
@log_decorator
async def get_holiday(date: str):
    """
    指定された日付が祝日かどうかを判定し、祝日名を返すAPI
    例: /api/check_holiday?date=2025/1/1
    """
    holiday_map = load_holiday_map()
    holiday_name = holiday_map.get(date)

    return JSONResponse(content={"holiday_name": holiday_name or ""})


# 配達可能曜日決定辞書 
# １店のみなのでconfigファイルにしなかった
delivery_mapping = {
    0: 1, # 月 -> 火
    1: 2, # 火 -> 水
    2: 4, # 水 -> 金
    3: 4, # 木 -> 金
    4: 5, # 金 -> 土
    5: 0, # 土 -> 月
    6: 0 # 日 -> 月
}

from datetime import datetime
from utils.decorator import log_decorator
from config.config_loader import search_delivery_date

@account_router.get(
    "/v1/delivery_date/{date_str}",
    summary="配達可能日の取得：共通",
    description=f"指定された日付（YYYY-MM-DD）から配達可能日を判定するAPI 例: /api/delivery_date?date=2025/1/1",
    tags=["util"]
)
@log_decorator
# async def delivery_date_view(date_str: str):
async def get_delivery_date(date_str: str):

    """
    指定された日付（YYYY-MM-DD）から配達可能日を判定するAPI
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    # 祝日をスキップ
    valid_date = await search_delivery_date(date)
    print(f"{valid_date}")

    # 曜日判定
    weekday = valid_date.weekday()  # 0: 月曜日 ～ 6: 日曜日
    delivery_day = delivery_mapping.get(weekday, "Invalid weekday")

    return {
        "order_date": valid_date.strftime("%Y-%m-%d"),
        "weekday": weekday,
        "delivery_day": delivery_day
    }

