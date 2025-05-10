# routers/shop.py
# ../shops/meになる
'''
    1. shop_view(request: Request, response: Response):
    2. get_shop_context(request: Request, orders):
    3. order_json(request: Request, days_ago: str = Query("0")):
'''
from fastapi import HTTPException, Query, Request, Response, APIRouter, status
from fastapi.responses import HTMLResponse
from venv import logger

from utils.helper import redirect_login_failure, redirect_unauthorized
from utils.utils import get_all_cookies, check_permission, log_decorator

from services.order_view import order_table_view, get_order_json
from models.order import select_orders_by_shop_all

from database.local_postgresql_database import endpoint, default_shop_name
from core.constants import ERROR_ILLEGAL_COOKIE

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

shop_router = APIRouter()


@shop_router.post("/me", response_class=HTMLResponse, tags=["shops"])
@shop_router.get("/me", response_class=HTMLResponse, tags=["shops"])
@log_decorator
async def shop_view(request: Request, response: Response):
    try:
        permits = [10, 99]
        if await check_permission(request, permits) == False:
            return redirect_unauthorized(request, "店舗ユーザー権限がありません。")

        cookies = get_all_cookies(request)
        if not cookies:
            logger.warning("shop_view - Cookieが取得できません")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_ILLEGAL_COOKIE#"Cookieが不正または取得できません"
            )

        orders = await select_orders_by_shop_all(default_shop_name)
        if orders is None:
            logger.debug('shop_view - 注文がありません')
            return HTMLResponse("<html><p>注文は0件です</p></html>")

        shop_context = await get_shop_context(request, orders)

    except HTTPException as e:
        logger.exception(f"HTTPException: {e.detail}")
        return redirect_login_failure(request, e.detail)
    except Exception as e:
        logger.exception("shop_viewで予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注文情報の取得中にサーバーエラーが発生しました"
        )
    else:
        return await order_table_view(response, orders, "shop.html", shop_context)


# @shop_router.post("/me", response_class=HTMLResponse, tags=["shops"])
# @shop_router.get("/me", response_class=HTMLResponse, tags=["shops"])
# @log_decorator
# async def shop_view(request: Request, response: Response):
#     # お弁当屋の注文確認
#     try:
#         permits = [10, 99]
#         if await check_permission(request, permits) == False:
#             return redirect_unauthorized(request, "店舗ユーザー権限がありません。")

#         cookies = get_all_cookies(request)
#         if not cookies:
#             raise CookieException(method_name="get_all_cookies()")

#         orders = await select_orders_by_shop_all(default_shop_name)
#         # print(f"shop_view() - orders: {orders}")
#         if orders is None:
#             logger.debug('shop_view - ordersなし')
#             return HTMLResponse("<html><p>注文は0件です</p></html>")

#         shop_context = await get_shop_context(request, orders)

#         return await order_table_view(response, orders, "shop.html", shop_context)


#     except CookieException as e:
#          return redirect_login_failure(request, ERROR_ILLEGAL_COOKIE, e)
#     except HTTPException as e:
#         return redirect_login_failure(request, e.detail)
#     except Exception as e:
#         raise CustomException(
#             status.HTTP_400_BAD_REQUEST,
#             f"/shop_view()",
#             f"Error: {str(e)}")


# async def get_shop_context(request: Request, orders):
#         # 備考：ここはtarget_urlをcontextに入れる改善が必要
#         # 更に、order_table_view()も引数を2個にできる(response, shop_context)
#         shop_context = {
#             'request': request,
#             'base_url': endpoint,
#         }
#         order_context = {
#             'orders': orders,
#             'order_count': len(orders),
#             "order_details": orders[0].model_dump() if orders else None
#         }

#         shop_context.update(order_context)

#         return shop_context
async def get_shop_context(request: Request, orders):
    try:
        shop_context = {
            'request': request,
            'base_url': endpoint,
        }
        order_context = {
            'orders': orders,
            'order_count': len(orders),
            "order_details": orders[0].model_dump() if orders else None
        }

        shop_context.update(order_context)

    except (AttributeError, TypeError) as e:
        logger.exception("get_shop_context - 注文データ形式不正")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="注文データが不正です"
        )
    except Exception as e:
        logger.exception("get_shop_context - 予期せぬエラー")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注文情報取得中にサーバーエラーが発生しました"
        )
    else:
        return shop_context


# @shop_router.get("/me/order_json",response_class=HTMLResponse, tags=["shops"]) 
# @log_decorator
# async def order_json(request: Request, days_ago: str = Query("0")):
#     # services/order_view.pyにある
#     return await get_order_json(request, days_ago)
@shop_router.get("/me/order_json", response_class=HTMLResponse, tags=["shops"])
@log_decorator
async def order_json(request: Request, days_ago: str = Query("0")):
    try:
        return await get_order_json(request, days_ago)

    except HTTPException as e:
        logger.exception(f"order_json - HTTPException: {e.detail}")
        return HTMLResponse(f"エラー: {e.detail}", status_code=e.status_code)

    except Exception as e:
        logger.exception("order_json - 予期せぬエラー")
        return HTMLResponse("注文データ取得中に予期せぬエラーが発生しました", status_code=500)


from fastapi import BackgroundTasks, Query
from fastapi.responses import JSONResponse

@shop_router.get("/filter_order_logs", tags=["shops"])
async def filter_order_logs(background_tasks: BackgroundTasks, shop: str = Query(...)):
    def run_log_filter():
        import subprocess
        subprocess.run(
            ["python", "order_log_filter_config.py", "order_logs", shop],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    background_tasks.add_task(run_log_filter)

    return JSONResponse(content={"message": "ログ抽出処理をバックグラウンドで開始しました"})


# @shop_router.get("/filter_order_logs", tags=["shops"])
# async def filter_order_logs(shop: str = Query(...)):
#     try:
#         process = await asyncio.create_subprocess_exec(
#             "python", "order_log_filter_config.py", "order_logs", shop,
#             stdout=asyncio.subprocess.PIPE,
#             stderr=asyncio.subprocess.PIPE
#         )
#         stdout, stderr = await process.communicate()
#         return JSONResponse(content={
#             "stdout": stdout.decode(),
#             "stderr": stderr.decode()
#         })
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"error": str(e)})

# import subprocess
# @shop_router.get("/filter_order_logs", tags=["shops"])
# async def filter_order_logs(shop: str = Query(...)):
#     """
#     注文ログを指定されたショップ名でフィルタし、combined_ログを生成
#     """
#     try:
#         # Pythonスクリプトを呼び出してフィルタ処理を実行
#         result = subprocess.run(
#             ["python", "order_log_filter_config.py", "order_logs", shop],
#             capture_output=True,
#             text=True,
#             timeout=10
#         )
#         return JSONResponse(content={
#             "stdout": result.stdout,
#             "stderr": result.stderr
#         })
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"error": str(e)})

from fastapi.responses import HTMLResponse
import os

@shop_router.get("/order_logs", response_class=HTMLResponse, tags=["shops"])
async def list_combined_order_logs():
    """combined_ログのみをリスト表示"""
    log_dir = "order_logs"
    if not os.path.exists(log_dir):
        return "<h1>注文ログディレクトリが存在しません</h1>"

    # combined_ で始まるファイルだけ抽出
    log_files = sorted(
        [f for f in os.listdir(log_dir) if f.startswith("combined_")],
        reverse=True
    )

    if not log_files:
        return "<h1>表示可能な注文ログがありません</h1>"

    links = [f"<li><a href='/shops/order_logs/{file}'>{file}</a></li>" for file in log_files]
    return f"<h1>結合注文ログ一覧</h1><ul>{''.join(links)}</ul>"

@shop_router.get("/order_logs/{filename}", response_class=HTMLResponse, tags=["shops"])
async def view_combined_order_log(filename: str):
    """選択された結合ログファイルを表示"""
    log_path = os.path.join("order_logs", filename)

    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read().replace('\n', '<br>')
            return f"<h1>{filename}</h1><pre>{content}</pre>"
        else:
            return HTMLResponse("ログファイルが存在しません。", status_code=404)

    except Exception as e:
        return HTMLResponse(f"読み込み中にエラーが発生しました: {str(e)}", status_code=500)

from fastapi.responses import HTMLResponse

@shop_router.get("/order_logs", response_class=HTMLResponse, tags=["shops"])
async def list_combined_order_logs():
    """combined_ログファイルのみを表示する（店舗ユーザー専用）"""
    log_dir = "order_logs"
    if not os.path.exists(log_dir):
        return "<h1>注文ログディレクトリが存在しません</h1>"

    # combined_で始まるファイルのみ抽出
    log_files = sorted(
        [f for f in os.listdir(log_dir) if f.startswith("combined_")],
        reverse=True
    )

    if not log_files:
        return "<h1>結合注文ログは見つかりませんでした</h1>"

    links = [f"<li><a href='/shops/order_logs/{f}'>{f}</a></li>" for f in log_files]
    return f"<h1>注文ログ（店舗用）</h1><ul>{''.join(links)}</ul>"


@shop_router.get("/order_logs/{filename}", response_class=HTMLResponse, tags=["shops"])
async def view_combined_order_log(filename: str):
    """指定されたログファイルを表示"""
    log_path = os.path.join("order_logs", filename)
    if not os.path.exists(log_path):
        return HTMLResponse("ログファイルが存在しません", status_code=404)

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read().replace("\n", "<br>")
    return f"<h1>{filename}</h1><pre>{content}</pre>"
