import asyncio
import os
from fastapi import Depends, FastAPI, Form, Header, Query, Response, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
import tracemalloc
from typing import Optional

import jwt
from pydantic import BaseModel
from starlette import status

from local_jwt_module import SECRET_KEY, get_new_token, check_cookie_token

from database.sqlite_database import SQLException, init_database, insert_new_user, select_user, update_order, update_user, select_shop_order, select_user, insert_order
from schemas.schemas import User
from utils.utils import prevent_order_twice, stop_twice_order, compare_expire_date, delete_all_cookies, log_decorator, set_all_cookies, get_all_cookies, log_decorator
from utils.exception import CustomException

from services.order_view import order_table_view

# tracemallocを有効にする
tracemalloc.start()

ALGORITHM = "HS256"

from services.router import router
from services.admin import admin_router
from services.manager import manager_router
from shop import shop_router
#from routers.user import user_router
app = FastAPI()

app.include_router(router, prefix="/api")
app.include_router(admin_router, prefix="/admin")
app.include_router(manager_router, prefix="/manager")
app.include_router(shop_router, prefix="/shops")
#app.include_router(user_router, prefix="/users")

templates = Jinja2Templates(directory="templates")
from fastapi.staticfiles import StaticFiles



endpoint = 'https://127.0.0.1:8000'

# login.htmlに戻る
def redirect_login(request: Request, message: str):
    try:
        print("login")
        return templates.TemplateResponse("login.html", {"request": request, "message": message})
    except HTTPException as e:
        raise
    except Exception as e:
        raise CustomException(status.HTTP_404_NOT_FOUND, f"redirect_login() Error:  {e.detail}")

# 例外ハンドラーの設定
# 実装例
# raise CustomException(400, "token の有効期限が切れています。再登録をしてください。")
@app.exception_handler(CustomException)
async def custom_exception_handler(
    request: Request, exc: CustomException):
    print(f"例外ハンドラーが呼ばれました: {exc.detail}")  # デバッグ用
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "message": exc.detail},
        status_code=exc.status_code
    )
# -----------------------------------------------------
# エントリポイント
@app.get("/", response_class=HTMLResponse)
@log_decorator
async def root(request: Request, response: Response):

    # テストデータ作成
    #await init_database()

    if(stop_twice_order(request)):
        last_order = request.cookies.get('last_order_date')
        message = f"<html><p>きょう２度目の注文です。</p><a>last order: {last_order} </a><a href='{endpoint}/clear'>Cookieを消去</a></html>"

        return HTMLResponse(message)


    # token チェックの結果を取得
    token_result = check_cookie_token(request)
    #print(f"token_result: {token_result}")

    if token_result is None:
        #raise CustomException(400, "トークンの有効期限が切れています。再登録をしてください。")
        #print("token_result: ありません")
        message = f"token の有効期限が切れています。再登録をしてください。{endpoint}"
        return templates.TemplateResponse("login.html", {"request": request, "message": message})

    # もし token_result がタプルでなければ（＝TemplateResponse が返されているなら）、そのまま返す
    if not isinstance(token_result, tuple):
        return token_result
    else:
        token, exp = token_result

    try:
        if compare_expire_date(exp):
            raise CustomException(400, f"トークンの有効期限が切れています。再登録をしてください。{endpoint}")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        #print(f"jwt.decode: {payload}")
        username = payload['sub']
        permission = payload['permission']
        exp = payload['exp']
        #print(f"exp: {exp}")
        #print("token is not expired.")

        response = RedirectResponse(url="/order_complete", status_code=303)

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

    except jwt.ExpiredSignatureError:
        raise CustomException(status.HTTP_400_BAD_REQUEST, "トークンの有効期限が切れています。再登録をしてください。")

    except jwt.InvalidTokenError:
        raise CustomException(status.HTTP_400_BAD_REQUEST, "無効なトークンです")


# ログイン画面を表示するエンドポイント
@app.get("/login", response_class=HTMLResponse)
@log_decorator
async def login_get(request: Request):
#async def login_get(request: Request, message: Optional[str] = ""):
    try:
        redirect_login(request, "ようこそ")

    except Exception as e:
        raise CustomException(status.HTTP_404_NOT_FOUND, f"login_get() Error:  {e.detail}")

# -----------------------------------------------------
# ログイン認証
@log_decorator
async def authenticate_user(username, password) -> Optional[User]:
    try:
        user = await select_user(username)

        if user is None:
            #print(f"username: {user.username}")
            await insert_new_user(username, password, 'name')
            user = await select_user(username)

        #print(f"username: {user.username}")
        if user.get_password() != password:
            return None

        data = {
            "sub": user.get_username(),
            "permission": user.get_permission()
        }
        access_token, utc_dt_str = get_new_token(data)

        user.set_token(access_token)
        #print(f"access_token: {access_token}")
        user.set_exp(utc_dt_str)
        #print(f"expires: {utc_dt_str}")
        #print(f"user: {user}")
        return user

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(status.HTTP_405_METHOD_NOT_ALLOWED, f"authenticate_user() 予期せぬエラーが発生しました。{e.detail}")

# ログインPOST
@app.post("/login", response_class=HTMLResponse)
@log_decorator
async def login_post(response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        username = form_data.username
        password = form_data.password

        user = await authenticate_user(username, password) 
        #print(f"user: {user}")
        if user is None:
            raise CustomException(status.HTTP_404_NOT_FOUND, f"user:{user} 取得に失敗しました")

        #print("username と password一致")

        # リダイレクト前
        permission = user.get_permission()

        # prefix込みでリダイレクト
        redirect_url = {
            1: "/order_complete",
            2: "/manager/today",
            10: "/shops/today",
            99: "/admin/today"}.get(permission, "/error")
        print(f"redirect_url: {redirect_url}")

        response = RedirectResponse(
            url=redirect_url, status_code=303)

        #print("ここまできた 1")
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


        set_all_cookies(response, data)

        #user.print_max_age_str()

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
        raise CustomException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"/login_post() 予期せぬエラーが発生しました: {str(e)}")


# お弁当の注文完了　ユーザーのみ
@app.get("/order_complete",response_class=HTMLResponse) 
@log_decorator
async def regist_complete(request: Request, response: Response): 
#async def regist_complete(request: Request, response: Response,
#                    hx_request: Optional[str] = Header(None)): 
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            raise CustomException(status.HTTP_400_BAD_REQUEST, "Cookieが取得できませんでした。")

        # 注文追加
        user = await select_user(cookies['sub'])

        if user is None:
            #print(f"user:{user} 取得に失敗しました")
            raise CustomException(status.HTTP_400_BAD_REQUEST, f"user:{user} 取得に失敗しました")

        await insert_order(
            user.company_id,
            user.username,
            user.shop_name,
            user.menu_id,
            amount=1)

        orders = await select_shop_order(
            user.shop_name, -7, user.username)

        if orders is None or len(orders) == 0:
            print("No orders found or error occurred.")
            raise CustomException(status.HTTP_400_BAD_REQUEST, "注文が見つかりません")

        #await show_all_orders()
        order_count = len(orders) - 1
        last_order_date = orders[order_count].created_at
        #last_order_date = orders[0].created_at # DESCの場合
        prevent_order_twice(response, last_order_date)
        
        main_view = "order_complete.html"
        return await order_table_view(request, response, orders, main_view)

    except SQLException as e:
        raise
    except HTTPException as e:
        raise
    except Exception as e:
        print(f"/order_complete Error: {str(e)}")
        raise CustomException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"予期せぬエラーが発生しました: {str(e)}")


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

@app.post("/update_cancel_status")
@log_decorator
async def update_cancel_status(update: CancelUpdate):
    try:
        results = []
        for change in update.updates:
            order_id = change["order_id"]
            canceled = change["canceled"]
            print(f"更新 order_id: {order_id}, canceled: {canceled}")

            # ここに SQL の UPDATE 文を実行するコードを入れる
            # 例: await database.execute("UPDATE orders SET canceled = $1 WHERE order_id = $2", canceled, order_id)
            await update_order(order_id, canceled)
            results.append({"order_id": order_id, "canceled": canceled, "success": True})
        
        return {"results": results}
    except Exception as e:
        print(f"/update_cancel_status Error: {str(e)}")
        raise CustomException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"予期せぬエラーが発生しました: {str(e)}")

# 例外テスト
@app.get("/test_exception")
async def test_exception():
    raise CustomException(400, "これはテストエラーです")

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
if __name__ == "__main__":
    import asyncio
    import uvicorn

    # Windows環境向けのイベントループポリシーを最初に設定
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Uvicornの起動
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=10, loop="asyncio")
