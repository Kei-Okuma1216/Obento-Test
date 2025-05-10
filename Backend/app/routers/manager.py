# routers/manager.py
# ../manager/meになる
'''
    1. manager_view(request: Request, response: Response):
    2. def get_manager_context(request: Request, orders):
    3. fax_order_sheet_view(request: Request):
    4. get_fax_sheet_context(request: Request):
'''
from fastapi import Request, Response, APIRouter, status, HTTPException
from fastapi.responses import HTMLResponse
from venv import logger

from utils.helper import redirect_unauthorized
from utils.utils import check_permission, get_all_cookies, log_decorator

from services.order_view import order_table_view
from models.order import select_orders_by_company_all

from database.local_postgresql_database import endpoint


from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

manager_router = APIRouter()




# 契約企業(お弁当担当者)画面
# 注意：エンドポイントにprefix:managerはつけない
# @manager_router.get("/me", response_class=HTMLResponse, tags=["manager"])
# @log_decorator
# async def manager_view(request: Request, response: Response):
#     try:
#         permits = [2, 99]
#         if await check_permission(request, permits) == False:
#             return redirect_unauthorized(request, "契約企業ユーザー権限がありません。")

#         cookies = get_all_cookies(request)
#         if not cookies:
#             raise CookieException(method_name="manager_view()")

#         # 会社の全注文
#         orders = await select_orders_by_company_all(company_id=1)

#         if orders is None:
#             logger.debug('ordersなし')
#             return HTMLResponse("<html><p>注文は0件です</p></html>")

#         target_url = "manager.html"
#         context = await get_manager_context(request, orders)

#         return await order_table_view(response, orders, target_url, context)

#     except CookieException as e:
#         raise
#     except Exception as e:
#         raise CustomException(
#             status.HTTP_400_BAD_REQUEST,
#             "/manager_view()",
#             f"Error: {str(e)}")
@manager_router.get("/me", response_class=HTMLResponse, tags=["manager"])
@log_decorator
async def manager_view(request: Request, response: Response):
    try:
        permits = [2, 99]
        if await check_permission(request, permits) == False:
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

    except HTTPException as e:
        logger.exception(f"manager_view - HTTPException: {e.detail}")
        return HTMLResponse(f"エラー: {e.detail}", status_code=e.status_code)
    except Exception as e:
        logger.exception("manager_view - 予期せぬエラーが発生しました")
        return HTMLResponse("注文情報の取得中にエラーが発生しました", status_code=500)
    else:
        return await order_table_view(response, orders, "manager.html", context)


# async def get_manager_context(request: Request, orders):

#     # 表示用データの作成
#     manager_context = {
#         'request': request,
#         'base_url': endpoint,
#     }
#     # 注文一覧タブ用のデータ
#     order_context = {
#         'orders': orders,
#         'order_count': len(orders),
#         "order_details": orders[0].model_dump() if orders else None
#     }
#     # FAX情報タブ用のデータ
#     fax_context = {
#         "shop_name": "はーとあーす勝谷",
#         "menu_name": "お昼のお弁当",
#         "price": 450,
#         "order_count": 6,
#         "total_amount": 450*6,
#         "facility_name": "テンシステム",
#         "POC": "林"
#     }
#     manager_context.update(order_context)
#     manager_context.update(fax_context)

#     return manager_context
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


# @manager_router.get("/me/fax_order_sheet", response_class=HTMLResponse, tags=["manager"])
# @log_decorator
# async def fax_order_sheet_view(request: Request):

#     target_url = "fax_order_sheet.html"
#     context = await get_fax_sheet_context(request)

#     return templates.TemplateResponse(target_url, {"request": request, **context})
@manager_router.get("/me/fax_order_sheet", response_class=HTMLResponse, tags=["manager"])
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
        return templates.TemplateResponse("fax_order_sheet.html", {"request": request, **context})


# async def get_fax_sheet_context(request: Request):
    
#     fax_context = {
#          "shop_name": request.query_params.get("shop_name"),
#          "menu_name": request.query_params.get("menu_name"),
#          "price": request.query_params.get("price"),
#          "order_count": request.query_params.get("order_count"),
#          "total_amount": request.query_params.get("total_amount"),
#          "facility_name": request.query_params.get("facility_name"),
#          "POC": request.query_params.get("POC"),
#          "delivery_year": request.query_params.get("delivery_year"),
#          "delivery_month": request.query_params.get("delivery_month"),
#          "delivery_day": request.query_params.get("delivery_day"),
#          "delivery_weekday": request.query_params.get("delivery_weekday")
#     }
#     return fax_context
async def get_fax_sheet_context(request: Request):
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

