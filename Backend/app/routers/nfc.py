# routers/nfc.py
''' 関数一覧
    1. handle_nfc_order(tag_id: str, request: Request):
    2. handle_order(tag_id: str, request: Request):
    3. handle_cancel(request: Request):
'''
''' NFCタグ一覧
    #nfc-001    テンシステム用 注文タグNo1
    #nfc-002    テンシステム用 キャンセルタグ
'''
from fastapi import Request, APIRouter

nfc_api_router = APIRouter(
    tags=["nfc"]
)

# NFCアクセス
@nfc_api_router.get(
    "/nfc/{tag_id}",
    summary="NFCタグ共通入口",
    description="NFCタグを読み取った際の共通エンドポイントです。")
async def handle_nfc_order(tag_id: str, request: Request):
    if tag_id == "cancel":
        return await handle_cancel(request)
    else:
        return await handle_order(tag_id, request)

async def handle_order(tag_id: str, request: Request):
    raise NotImplementedError

async def handle_cancel(request: Request):
    raise NotImplementedError
