# routers/manager.py
'''
    1. manager_view(request: Request, response: Response):
    2. get_manager_context(request: Request, orders):
    3. fax_order_sheet_view(request: Request):
    4. get_fax_sheet_context(request: Request):
'''
from fastapi import Request, Response, APIRouter, status, HTTPException
from fastapi.responses import HTMLResponse
from venv import logger

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

manager_router = APIRouter()


from utils.helper import redirect_unauthorized
from utils.utils import log_decorator
from utils.permission_helper import check_permission
from utils.cookie_helper import get_all_cookies


from services.order_view import order_table_view
from models.order import select_orders_by_company_all
from database.local_postgresql_database import endpoint

# 契約企業(お弁当担当者)画面
# 注意：エンドポイントにprefix:managerはつけない
@manager_router.get(
    "/{manager_id}",
    summary="メイン画面：契約企業ユーザー",
    description="days_ago:intより指定日数前の注文情報を取得後、JSON形式で表示する。",
    response_class=HTMLResponse,
    tags=["manager"]
)
@log_decorator
async def manager_view(request: Request, response: Response, manager_id: str):
    try:
        if await check_permission(request, [2]) == False:
            return redirect_unauthorized(request, "契約企業ユーザー権限がありません。")

        cookies = get_all_cookies(request)
        if not cookies:
            logger.warning("manager_view - Cookieが取得できません")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cookieが不正または取得できません"
            )

        orders = await select_orders_by_company_all(company_id=1)
        if not orders:
            logger.debug('manager_view - 注文なし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")

        context = await get_manager_context(request, orders)

        # CookieからユーザーID（manager_id）取得
        cookies = get_all_cookies(request)
        
        # print(f"manager_view - context username: {manager_id}")
        context.update({"username": manager_id,
                        "manager_id": manager_id
                        })

    except HTTPException as e:
        logger.exception(f"manager_view - HTTPException: {e.detail}")
        return HTMLResponse(f"エラー: {e.detail}", status_code=e.status_code)
    except Exception as e:
        logger.exception("manager_view - 予期せぬエラーが発生しました")
        return HTMLResponse("注文情報の取得中にエラーが発生しました", status_code=500)
    else:
        return await order_table_view(request, response, orders, "manager.html", context)
        # return templates.TemplateResponse("manager.html", context) # これでも動いた

async def get_manager_context(request: Request, orders):
    try:
        manager_context = {
            'request': request,
            'base_url': endpoint,
        }

        order_context = {
            'orders': orders,
            'order_count': len(orders),
            "order_details": orders[0].model_dump() if orders else None
        }

        fax_context = {
            "shop_name": "はーとあーす勝谷",
            "menu_name": "お昼のお弁当",
            "price": 450,
            "order_count": 6,
            "total_amount": 450 * 6,
            "facility_name": "テンシステム",
            "POC": "林"
        }

        manager_context.update(order_context)
        manager_context.update(fax_context)

    except (AttributeError, TypeError) as e:
        logger.exception("get_manager_context - データ整形中にエラー")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="表示データ作成中にエラーが発生しました"
        )
    except Exception as e:
        logger.exception("get_manager_context - 予期せぬエラー")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注文情報の表示準備中にサーバーエラーが発生しました"
        )
    else:
        return manager_context


@manager_router.get(
    "/me/fax_order_sheet",
    summary="FAX注文用紙表示画面：契約企業ユーザー",
    description="メイン画面のFAX注文タブの入力を元にして、FAX注文用紙をプレビュー形式で表示する。",
    response_class=HTMLResponse,
    tags=["manager"],
    include_in_schema=False)
@log_decorator
async def fax_order_sheet_view(request: Request):
    try:
        context = await get_fax_sheet_context(request)
        
    except HTTPException as e:
        logger.exception(f"fax_order_sheet_view - HTTPException: {e.detail}")
        return HTMLResponse(f"エラー: {e.detail}", status_code=e.status_code)
    except Exception as e:
        logger.exception("fax_order_sheet_view - 予期せぬエラーが発生しました")
        return HTMLResponse("FAXシート表示中にエラーが発生しました", status_code=500)
    else:
        return templates.TemplateResponse(
            "fax_order_sheet.html", {"request": request, **context})

@manager_router.get(
    "/{manager_id}/fax_order_sheet",
    summary="FAX注文用紙表示画面：契約企業ユーザー",
    description="契約企業IDに基づいてFAX注文用紙をプレビュー形式で表示する。",
    response_class=HTMLResponse,
    tags=["manager"]
)
@log_decorator
async def fax_order_sheet_view(request: Request, manager_id: int):
    try:
        # manager_id を使うよう get_fax_sheet_context が対応しているなら引数に渡す
        context = await get_fax_sheet_context(request, manager_id=manager_id)

    except HTTPException as e:
        logger.exception(f"fax_order_sheet_view - HTTPException: {e.detail}")
        return HTMLResponse(f"エラー: {e.detail}", status_code=e.status_code)

    except Exception as e:
        logger.exception("fax_order_sheet_view - 予期せぬエラーが発生しました")
        return HTMLResponse("FAXシート表示中にエラーが発生しました", status_code=500)

    else:
        return templates.TemplateResponse(
            "fax_order_sheet.html", {"request": request, **context}
        )


# async def get_fax_sheet_context(request: Request):
async def get_fax_sheet_context(request: Request, manager_id: int):
    try:
        fax_context = {key: request.query_params.get(key) for key in [
            "shop_name", "menu_name", "price", "order_count", "total_amount",
            "facility_name", "POC", "delivery_year", "delivery_month",
            "delivery_day", "delivery_weekday"
        ]}

        if not any(fax_context.values()):
            logger.warning("get_fax_sheet_context - クエリパラメータが不足しています")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FAXシートの必要なパラメータが不足しています"
            )

    except HTTPException as e:
        raise
    except Exception as e:
        logger.exception("get_fax_sheet_context - 予期せぬエラー")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FAXシート情報の取得中にサーバーエラーが発生しました"
        )
    else:
        return fax_context

