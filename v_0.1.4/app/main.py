import asyncio
import os
import sys
from fastapi import Depends, FastAPI, Form, Header, Query, Response, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
import tracemalloc
import jwt
from pydantic import BaseModel
from starlette import status
from typing import Optional

from local_jwt_module import SECRET_KEY, ALGORITHM, get_new_token, check_cookie_token

from database.sqlite_database import SQLException, get_connection, init_database, insert_new_user, select_user, update_order, update_user, select_shop_order, select_user, insert_order

from utils.utils import prevent_order_twice, stop_twice_order, compare_expire_date, delete_all_cookies, log_decorator, set_all_cookies, get_all_cookies, log_decorator
from utils.exception import CookieException, CustomException, TokenExpiredException

from schemas.schemas import User

from services.order_view import order_table_view

# tracemallocを有効にする
tracemalloc.start()

from log_config import logger  # 先ほどのログ設定をインポート

from routers.router import sample_router
from routers.admin import admin_router
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



endpoint = 'https://127.0.0.1:8000'

# login.htmlに戻る
@log_decorator
def redirect_login(request: Request, message: str):
    try:
        logger.debug("redirect_login()")

        return templates.TemplateResponse("login.html", {"request": request, "message": message})
    except HTTPException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_404_NOT_FOUND,
            "redirect_login()",
            f"Error: {e.detail}")

# -----------------------------------------------------
# エントリポイント
@app.get("/", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def root(request: Request, response: Response):

    logger.info(f"root() - ルートにアクセスしました")
    # テストデータ作成
    #await init_database()

    if(stop_twice_order(request)):
        last_order = request.cookies.get('last_order_date')
        message = f"<html><p>きょう２度目の注文です。</p><a>last order: {last_order} </a><a href='{endpoint}/clear'>Cookieを消去</a></html>"
        logger.info(f"stop_twice_order() - きょう２度目の注文を阻止")

        return HTMLResponse(message)


    # token チェックの結果を取得
    token_result = check_cookie_token(request)
    logger.debug(f"token_result: {token_result}")

    if token_result is None:
        # 備考：ここは例外に置き換えない。理由：画面が停止するため
        '''raise TokenExpiredException("check_cookie_token()")
        '''
        logger.debug("token_result: ありません")
        message = f"token の有効期限が切れています。再登録をしてください。{endpoint}"

        return templates.TemplateResponse("login.html", {"request": request, "message": message})
        
    # もし token_result がタプルでなければ（＝TemplateResponse が返されているなら）、そのまま返す
    if not isinstance(token_result, tuple):
        return token_result
    else:
        token, exp = token_result

    try:
        if compare_expire_date(exp):
            raise TokenExpiredException("compare_expire_date()")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"jwt.decode: {payload}")

        username = payload['sub']
        permission = payload['permission']
        exp = payload['exp']

        logger.debug(f"sub: {username}, permission: {permission}, exp: {exp}")
        logger.debug("token is not expired.")


        response = RedirectResponse(
            url="/order_complete",
            status_code=status.HTTP_303_SEE_OTHER)

        data = {
            "sub": username,
            "permission": permission,
        }
        access_token, exp = get_new_token(data)
        new_data = {
            "sub": username,
            "permission": permission,
            "exp": exp,
            "token": access_token
        }

        set_all_cookies(response, new_data)

        return response

    except TokenExpiredException as e:
        raise
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException("root()")
    except jwt.InvalidTokenError:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            "root()",
            "無効なトークンです")

# ログイン画面を表示するエンドポイント
@app.get("/login", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def login_get(request: Request):
    try:
        redirect_login(request, "ようこそ")

    except Exception as e:
        raise CustomException(
            status.HTTP_404_NOT_FOUND,
            "login_get()",
            f"Error:  {e.detail}")

# -----------------------------------------------------
# ログイン認証
@log_decorator
async def authenticate_user(username, password) -> Optional[User]:
    try:
        user = await select_user(username)

        if user is None:
            logger.debug(f"username: {user.username}")
            await insert_new_user(username, password, 'name')
            user = await select_user(username)

        logger.debug(f"username: {user.username}")
        if user.get_password() != password:
            return None

        data = {
            "sub": user.get_username(),
            "permission": user.get_permission()
        }
        access_token, utc_dt_str = get_new_token(data)
        user.set_token(access_token)        
        user.set_exp(utc_dt_str)

        logger.debug(f"access_token: {access_token}")        
        logger.debug(f"expires: {utc_dt_str}")
        logger.debug(f"user: {user}")
        logger.debug(f"authenticate_user() - userを正常に取得した")

        return user

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            f"authenticate_user()",
            f"予期せぬエラーが発生しました。{e.detail}")

# ログインPOST
@app.post("/login", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def login_post(response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        username = form_data.username
        password = form_data.password

        user = await authenticate_user(username, password) 
        logger.debug(f"user: {user}")
        if user is None:
            raise CustomException(
                status.HTTP_404_NOT_FOUND,
                "login_post()",
                f"user:{user} 取得に失敗しました")

        logger.debug("username と password一致")

        # リダイレクト前
        permission = user.get_permission()

        # prefix込みでリダイレクト
        redirect_url = {
            1: "/order_complete",
            2: "/manager/me",
            10: "/shops/me",
            99: "/admin/me"}.get(permission, "/error")
        logger.debug(f"redirect_url: {redirect_url}")

        response = RedirectResponse(
            url=redirect_url, status_code=303)

        data = {
            'sub': user.get_username(),
            'token': user.get_token(),
            'exp': user.get_exp(),
            'permission': user.get_permission()
        }
        #print(f" 'sub': {user.get_username()}")
        #print(f" 'token': {user.get_token()}")
        #print(f" 'exp': {user.get_exp()}")
        #print(f" 'permission': {user.get_permission()}")
        logger.debug(f"login_post() - 'sub': {user.get_username()}")
        logger.debug(f"login_post() - 'token': {user.get_token()}")
        logger.debug(f"login_post() - 'exp': {user.get_exp()}")
        logger.debug(f"login_post() - 'permission': {user.get_permission()}")
                     


        set_all_cookies(response, data)

        # トークンのsave
        username = user.get_username()
        await update_user(username, "token", user.get_token())
        await update_user(username, "exp", user.get_exp())

        return response
    
    except SQLException as e:
        raise
    except HTTPException as e:
        raise
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

        # 注文追加
        user = await select_user(cookies['sub'])

        if user is None:
            raise CustomException(
                status.HTTP_400_BAD_REQUEST,
                "regist_complete()",
                f"user:{user} 取得に失敗しました")

        await insert_order(
            user.company_id,
            user.username,
            user.shop_name,
            user.menu_id,
            amount=1)

        orders = await select_shop_order(
            user.shop_name, -7, user.username)

        logger.debug(f"orders: {orders}")
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
        
        main_view = "order_complete.html"
        return await order_table_view(
            request, response, orders, main_view)

    except SQLException as e:
        raise
    except HTTPException as e:
        raise
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



from typing import List

class CancelUpdate(BaseModel):
    updates: List[dict]  # 各辞書は {"order_id": int, "canceled": bool} の形式

from services.order_view import batch_update_orders

@app.post("/update_cancel_status")
@log_decorator
async def update_cancel_status(update: CancelUpdate):
    try:
        #change_cancel_status(update)
        return await batch_update_orders(update.updates)
    except Exception as e:
        raise 

'''
@app.post("/update_cancel_status")
@log_decorator
async def update_cancel_status(update: CancelUpdate):
    try:
        logger.info(f"update_cancel_status() - orderチェック変更")

        results = []
        for change in update.updates:
            order_id = change["order_id"]
            canceled = change["canceled"]
            logger.debug(f"更新 order_id: {order_id}, canceled: {canceled}")

            await update_order(order_id, canceled)

            results.append({"order_id": order_id, "canceled": canceled, "success": True})
        
        return {"results": results}

    except Exception as e:
        logger.debug(f"/update_cancel_status Error: {str(e)}")
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "update_cancel_status()",
            f"予期せぬエラーが発生しました: {str(e)}")'''
'''
async def change_cancel_status(update: CancelUpdate):
    try:
        logger.info(f"update_cancel_status() - orderチェック変更")

        results = []
        for change in update.updates:
            order_id = change["order_id"]
            canceled = change["canceled"]
            logger.debug(f"更新 order_id: {order_id}, canceled: {canceled}")

            await update_order(order_id, canceled)

            results.append({"order_id": order_id, "canceled": canceled, "success": True})
        
        return {"results": results}

    except Exception as e:
        logger.debug(f"/update_cancel_status Error: {str(e)}")
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "update_cancel_status()",
            f"予期せぬエラーが発生しました: {str(e)}")
'''

import aiosqlite
'''
async def batch_update_orders(updates: list[dict]):
    try:
        values = [(change["canceled"], change["order_id"]) for change in updates]
        sql = "UPDATE orders SET canceled = ? WHERE order_id = ?"

        conn = await get_connection()  # ✅ 非同期DB接続
        try:
            cur = await conn.cursor()  # ✅ `async with` は不要
            await cur.executemany(sql, values)  # ✅ `await` なし
            await conn.commit()  # ✅ コミットを実行
        finally:
            await conn.close()  # ✅ 明示的にクローズ

        return {"message": "Orders updated successfully"}

    except Exception as e:
        logger.error(f"batch_update_orders Error: {str(e)}")
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "batch_update_orders()",
            f"予期せぬエラー: {str(e)}")
'''




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

#app.mount("/static", StaticFiles(directory="static"), name="static")
# Ensure favicon.ico is accessible
@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    # ブラウザが要求するfaviconのエラーを防ぐ
    # https://github.com/fastapi/fastapi/discussions/11385
    favicon_path = './static/favicon.ico'  # Adjust path to file

    return FileResponse(favicon_path)
 
# Mount the directory where favicon.ico is located 
# faviconのマウント
#app.mount("/static", StaticFiles(directory="static"), name="static")
from fastapi.staticfiles import StaticFiles
static_path = os.path.join(os.path.dirname(__file__), "static")  # 絶対パスに変換
app.mount("/static", StaticFiles(directory=static_path), name="static")

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

