# routers/router.py
'''
    1. get_account_or_404_response(username: str):
    2. get_account_by_id_or_404_response(user_id: int):

    3. get_admin_account(request: Request):
    4. get_manager_account(request: Request, user_id: int = Query(...)):
    5. get_shop_account(request: Request, user_id: str = Query(...)):

    6. check_holiday(date: str):
    7. delivery_date_view(date_str: str):
'''
from fastapi import APIRouter

sample_router = APIRouter(
    tags=["sample"]
)


# 呼び方 お試しエンドポイント
# https://127.0.0.1:8000/api/items
@sample_router.get("/items/", tags=["sample"])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]


from fastapi import Request
from fastapi.responses import JSONResponse
from schemas.user_schemas import UserResponse
from utils.helper import redirect_unauthorized
from utils.utils import check_permission
from models.user import select_user

from fastapi import HTTPException, Query
from fastapi import Request, HTTPException

# ヘルパー
async def get_account_or_404_response(username: str):
    """
    ユーザー取得＆JSON返却を共通化。存在しない場合は404エラー。
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

from models.user import select_user_by_id

# 共通
async def get_account_by_id_or_404_response(user_id: int):
    user_info = await select_user_by_id(user_id)  # user_id で検索
    if user_info is None:
        raise HTTPException(status_code=404, detail=f"ユーザーID {user_id} が見つかりません")
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


# 管理者アカウント情報の取得
@sample_router.get("/v1/account/admin", response_model=UserResponse)
async def get_admin_account(request: Request):

    if not await check_permission(request, [99]):
        return redirect_unauthorized(request, "管理者権限がありません。")

    return await get_account_or_404_response("admin")


# 契約企業ユーザー情報の取得
@sample_router.get("/v1/account/manager", response_model=UserResponse)
async def get_manager_account(request: Request, user_id: int = Query(...)):

    if not await check_permission(request, [2]):
        return redirect_unauthorized(request, "マネージャー権限がありません。")

    return await get_account_by_id_or_404_response(user_id)


# 店舗ユーザー情報の取得
@sample_router.get("/v1/account/shop", response_model=UserResponse)
async def get_shop_account(request: Request, user_id: str = Query(...)):

    if not await check_permission(request, [10]):
        return redirect_unauthorized(request, "店舗権限がありません。")

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効なユーザーID")

    return await get_account_by_id_or_404_response(user_id_int)




'''--------------------------------------------------------------------------'''
from fastapi.responses import JSONResponse
from config.config_loader import load_holiday_map


@sample_router.get("/check_holiday")
async def check_holiday(date: str):
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
from utils.utils import log_decorator
from config.config_loader import skip_holiday


@sample_router.get("/delivery_date/{date_str}")
@log_decorator
async def delivery_date_view(date_str: str):
    """
    指定された日付（YYYY-MM-DD）から配達可能日を判定するAPI
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    # 祝日をスキップ
    valid_date = await skip_holiday(date)
    print(f"{valid_date}")

    # 曜日判定
    weekday = valid_date.weekday()  # 0: 月曜日 ～ 6: 日曜日
    delivery_day = delivery_mapping.get(weekday, "Invalid weekday")

    return {
        "order_date": valid_date.strftime("%Y-%m-%d"),
        "weekday": weekday,
        "delivery_day": delivery_day
    }

