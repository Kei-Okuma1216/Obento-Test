# routers/shop.py
# ../shops/4になる
# 引数が固定順に並べている
'''
    1. order_json(request: Request, days_ago: str = Query("0")):
    2. filter_order_logs(background_tasks: BackgroundTasks, shop: str = Query(...)):
    3. list_combined_order_logs():
    4. view_combined_order_log(filename: str):
    5. list_combined_order_logs():
    6. shop_view(request: Request, response: Response, shop_id: str):
    7. get_shop_context(request: Request, orders):
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




# JSON注文情報を取得する
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

# 注文ログを店舗名でフィルタする
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

# 注文ログを結合する
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

# 注文ログを表示する
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


# 注文ログを表示する
@shop_router.get("/order_logs/{filename}", response_class=HTMLResponse, tags=["shops"])
async def view_combined_order_log(filename: str):
    """指定されたログファイルを表示"""
    log_path = os.path.join("order_logs", filename)
    if not os.path.exists(log_path):
        return HTMLResponse("ログファイルが存在しません", status_code=404)

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read().replace("\n", "<br>")
    return f"<h1>{filename}</h1><pre>{content}</pre>"



from models.user import select_user_by_id

# 店舗メイン画面
@shop_router.get("/{shop_id}", response_class=HTMLResponse, tags=["shops"])
@shop_router.get("/{shop_id}", response_class=HTMLResponse, tags=["shops"])
@log_decorator
async def shop_view(request: Request, response: Response, shop_id: str):
    try:
        # 🚨 不正なID防御（Noneや非数値チェック）
        if not shop_id or shop_id.lower() == "none" or not shop_id.isdigit():
            logger.error("不正な shop_id が指定されました")
            return HTMLResponse("<html><p>不正な店舗IDが指定されました</p></html>", status_code=400)
        
        # 権限確認
        if await check_permission(request, [10, 99]) == False:
            return redirect_unauthorized(request, "店舗ユーザー権限がありません。")

        # ユーザー情報取得
        user_info = await select_user_by_id(int(shop_id))
        if user_info is None:
            logger.warning(f"ユーザーID {shop_id} が見つかりません")
            return HTMLResponse("<html><p>ユーザー情報が見つかりません</p></html>")

        # username（shop01）を取得
        shop_code = user_info.username

        # cookies = get_all_cookies(request)
        # if not cookies:
        #     logger.warning("shop_view - Cookieが取得できません")
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=ERROR_ILLEGAL_COOKIE#"Cookieが不正または取得できません"
        #     )

        # クッキーからユーザーID（shop_id）取得
        # shop_id = cookies.get("sub")
        # 上書きしない、URLパラメータの shop_id をそのまま使う
        # 注意：このshop_idはuser_idと共用している
        # print(f"shop_view - URLパラメータ shop_id: {shop_id}")

        # if not shop_id:
        #     logger.warning("shop_view - Cookie 'sub' が取得できません")
        #     return redirect_login_failure(request, "ログイン情報が取得できません。再度ログインしてください。")

        orders = await select_orders_by_shop_all(shop_code)
        if orders is None:
            logger.debug('shop_view - 注文がありません')
            return HTMLResponse("<html><p>注文は0件です</p></html>")


        shop_context = await get_shop_context(request, orders)
        shop_context.update({"username": shop_id})  # ここでユーザー名をテンプレートへ

        print(f"shop_view - context username: {shop_id}")
        shop_context.update({"username": shop_id, "shop_id": shop_id})


        return await order_table_view(request, response, orders, "shop.html", shop_context)

    except HTTPException as e:
        logger.exception(f"HTTPException: {e.detail}")
        return redirect_login_failure(request, e.detail)
    except Exception as e:
        logger.exception("shop_viewで予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注文情報の取得中にサーバーエラーが発生しました"
        )

# 店舗メイン画面コンテキスト取得
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
        return shop_context

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
