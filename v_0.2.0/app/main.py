# main.py
# 2.0 Bootstrap適用開始
import asyncio
import os
import sys
import jwt
from pydantic import BaseModel
from starlette import status
import tracemalloc
from typing import List

from fastapi import Depends, FastAPI, Response, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm


from local_jwt_module import SECRET_KEY, ALGORITHM, get_new_token

from database.sqlite_database import SQLException, init_database, insert_new_user, select_user, update_user, select_shop_order, select_user, insert_order

from utils.utils import get_token_expires, prevent_order_twice, compare_expire_date, delete_all_cookies, log_decorator, set_all_cookies, get_all_cookies, log_decorator, check_permission_and_stop_order
from utils.exception import CookieException, CustomException, NotAuthorizedException, TokenExpiredException
from utils.helper import *
from services.order_view import order_table_view
from schemas.schemas import UserBase, UserResponse

# tracemallocを有効にする
tracemalloc.start()

from log_config import logger  # 先ほどのログ設定をインポート

from routers.router import sample_router
from routers.admin import admin_router, update_existing_passwords
from routers.manager import manager_router
from routers.shop import shop_router
#from routers.user import user_router
app = FastAPI()

app.include_router(sample_router, prefix="/api")
app.include_router(admin_router, prefix="/admin")
app.include_router(manager_router, prefix="/manager")
app.include_router(shop_router, prefix="/shops")
#app.include_router(user_router, prefix="/users")

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")
from fastapi.staticfiles import StaticFiles

#from crud import hash_password, verify_password, get_user, create_user 

product_endpoint = 'https://192.168.3.19:8000'
develop_endpoint = 'https://127.0.0.1:8000'

# エントリポイントの選択
endpoint = product_endpoint


token_expired_error_message = "有効期限が切れています。再登録をしてください。"
forbid_second_order_message = "きょう２度目の注文です。重複注文により注文できません"


# -----------------------------------------------------
# エントリポイント
@app.get("/", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def root(request: Request, response: Response):

    try:
        logger.info(f"root() - ルートにアクセスしました")
        # テストデータ作成
        # 注意：データ新規作成後は、必ずデータベースのUserテーブルのパスワードを暗号化する
        await init_database() # 昨日の二重注文禁止が有効か確認する

        print("v_0.2.0")

        # 二重注文の禁止
        result , last_order = await check_permission_and_stop_order(request, response)
        logger.debug(f"result , last_order: {result , str(last_order)}")
        if result:
            message = f"<html><p>{forbid_second_order_message}</p><a>last order: {last_order} </a><br><a href='{endpoint}/clear'>Cookieを消去</a></html>"

            return HTMLResponse(message)

        # cookies チェック
        token = request.cookies.get("token")
        if token is None:
            ''' 備考：ここは例外に置き換えない。login.htmlへリダイレクトする。
                理由：画面が停止するため
            raise TokenExpiredException("check_cookie_token()")
            '''
            logger.debug("token: ありません")
            return redirect_login(request, "ようこそ")

        # token チェック
        expires = get_token_expires(request)

        if compare_expire_date(expires):
            # expires 無効
            return redirect_login(request, token_expired_error_message)
        else:
            # expires 有効
            logger.debug("token is not expired.")

        # token 解読
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload['sub']
        permission = payload['permission']

        main_url = await get_main_url(permission)

        return await create_auth_response(
            username, permission, main_url)

    except (TokenExpiredException, jwt.ExpiredSignatureError) as e:
        logger.error(e.detail["message"])
        return redirect_login(
            request, token_expired_error_message)
    except (CookieException, jwt.InvalidTokenError) as e:
        #logger.error(e.detail["message"])
        return redirect_error(
            request, token_expired_error_message, e)


# ログイン画面を表示するエンドポイント
@app.get("/login", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def login_get(request: Request):
    try:
        pass
        return redirect_login(request, "ようこそ")
    except Exception as e:
        return redirect_error(request, "ログインに失敗しました", e)

@app.post("/login", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def login_post(request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()):
    ''' ログインPOST '''
    try:
        username = form_data.username
        password = form_data.password

        user = await authenticate_user(username, password, '') 

        permission = user.get_permission()
        main_url = await get_main_url(permission)

        return await create_auth_response(user.get_username(), permission, main_url)

    except (NotAuthorizedException) as e:
        return redirect_login(request, "アクセス権限がありません。")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TokenExpiredException) as e:
        return redirect_login(request, token_expired_error_message)
    except (CookieException, SQLException, HTTPException) as e:
        return redirect_error(request, "login_post()", e)
    except Exception as e:
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "/login_post()",
            f"予期せぬエラーが発生しました: {str(e)}")


# お弁当の注文完了　ユーザーのみ
@app.get("/order_complete",response_class=HTMLResponse, tags=["users"]) 
@log_decorator
async def regist_complete(request: Request, response: Response): 
    try:
        cookies = get_all_cookies(request)

        user: UserResponse = await select_user(cookies['sub'])

        if user is None:
            raise SQLException("regist_complete()")

        await insert_order(
            user.company_id,
            user.username,
            user.shop_name,
            user.menu_id,
            amount=1)

        orders = await select_shop_order(
            user.shop_name, -7, user.username)

        #logger.debug(f"orders: {orders}")
        if orders is None or len(orders) == 0:
            logger.debug("No orders found or error occurred.")
            raise CustomException(
                status.HTTP_400_BAD_REQUEST,
                "regist_complete()",
                "注文が見つかりません")

        #await show_all_orders()
        order_count = len(orders) - 1
        last_order_date = orders[order_count].created_at
        #last_order_date = orders[0].created_at # DESCの場合
        prevent_order_twice(response, last_order_date)

        return await order_table_view(
            request, response, orders, "order_complete.html")

    except (SQLException, HTTPException) as e:
        return redirect_error(request, "注文確定に失敗しました", e)
    except Exception as e:
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "regist_complete()",
            f"予期せぬエラーが発生しました: {str(e)}")


# cookieを削除してログアウト
@app.get("/clear")
@log_decorator
async def clear_cookie(response: Response):
    response = RedirectResponse(url="/")

    delete_all_cookies(response)

    return response



class CancelUpdate(BaseModel):
    updates: List[dict]  # 各辞書は {"order_id": int, "canceled": bool} の形式

from services.order_view import batch_update_orders

@app.post("/update_cancel_status")
@log_decorator
async def update_cancel_status(update: CancelUpdate):
    ''' チェックの更新 '''
    try:
        return await batch_update_orders(update.updates)
    except Exception as e:
        raise 


# デバッグ用 例外ハンドラーの設定
@app.exception_handler(CustomException)
async def custom_exception_handler(
    request: Request, exc: CustomException):
    logger.error(f"例外ハンドラーが呼ばれました: {exc.detail}")  
    # 実装例
    # raise CustomException(400, "token の有効期限が切れています。再登録をしてください。")

    """カスタム例外をキャッチして、HTML にエラーを表示"""
    return templates.TemplateResponse(
        "error.html",  # templates/error.html を表示
        {"request": request, "message": exc.detail["message"], "status_code": exc.status_code},
        status_code=exc.status_code
    )

# デバッグ用 例外テスト
@app.get("/test_exception")
async def test_exception():
    logger.error("test_exception() testエラーが発生しました!")
    raise CustomException(
        status.HTTP_400_BAD_REQUEST,
        "test_exception()",
        "これはテストエラーです")


@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    # ブラウザが要求するfaviconのエラーを防ぐ
    # https://github.com/fastapi/fastapi/discussions/11385
    favicon_path = './static/favicon.ico'  # Adjust path to file

    return FileResponse(favicon_path)
 
# Mount the directory where favicon.ico is located 
# faviconのマウント
from fastapi.staticfiles import StaticFiles
static_path = os.path.join(os.path.dirname(__file__), "static")  # 絶対パスに変換
app.mount("/static", StaticFiles(directory=static_path), name="static")
# 備考：上記設定により環境変数PYTHONPATH設定は不要

# 他のモジュールでの誤使用を防ぐ
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    import asyncio
    import uvicorn

    # Windows環境向けのイベントループポリシーを最初に設定
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Uvicornの起動
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=10, loop="asyncio")
    LOGS_DIR = "./logs"

@app.get("/logs", response_class=HTMLResponse)
async def list_logs():
    # 入力例 https://127.0.0.0.1:8000/logs/2025-03-10
    # 備考　現在誰でもログにアクセスできる
    """logs フォルダ内のログファイル一覧を表示"""
    if not os.path.exists(LOGS_DIR):
        return "<h1>No logs found</h1>"

    files = sorted(os.listdir(LOGS_DIR), reverse=True)  # 最新のログを上に
    file_links = [f'<a href="/logs/{file}">{file}</a><br>' for file in files]

    return "<h1>Log Files</h1>" + "".join(file_links)

@app.get("/logs/{filename}")
async def read_log(filename: str):
    """指定されたログファイルの内容をHTMLで表示"""
    filepath = os.path.join(LOGS_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Log file not found")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f"<h1>{filename}</h1><pre>{f.read()}</pre>"

    return HTMLResponse(content)

