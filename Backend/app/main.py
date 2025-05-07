# Backend/app/main.py
# 2.3 システムテスト完了
'''ページ・ビュー・関数
    1. root(request: Request, response: Response):
    2. login_get(request: Request):
    3. login_post(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):

    4. clear_cookie(response: Response):

    5. class CancelUpdate(BaseModel):
        updates: List[dict]  # 各辞書は {"order_id": int, "canceled": bool} の形式
    6. update_cancel_status(update: CancelUpdate):

    7. custom_exception_handler(request: Request, exc: CustomException):
    8. test_exception():

    9. favicon():
    10. list_logs():
    11. read_log(filename: str):
'''
from fastapi import Depends, FastAPI, Response, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

from utils.helper import create_auth_response, get_main_url, redirect_error
from utils.utils import *
from utils.exception import *
from sqlalchemy.exc import DatabaseError
from log_unified import logger

from routers.router import sample_router
from routers.admin import admin_router
from routers.manager import manager_router
from routers.shop import shop_router
from routers.user import user_router

app = FastAPI()

# CORS対策
from fastapi.middleware.cors import CORSMiddleware
# 開発環境用：すべてのドメインを許可　routerの前の位置に記載すること
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],  # 全HTTPメソッドを許可（GET, POST, etc.）
    allow_headers=["*"],  # すべてのヘッダーを許可
)

app.include_router(sample_router, prefix="/api")
app.include_router(admin_router, prefix="/admin")
app.include_router(manager_router, prefix="/manager")
app.include_router(shop_router, prefix="/shops")
app.include_router(user_router, prefix="/users")

# 例外ハンドラーを登録
from utils.handlers import register_exception_handlers, test_exception_router  # 追加！
register_exception_handlers(app) # 例外ハンドラー登録
app.include_router(test_exception_router) # テストルーター登録（任意）


# エントリポイントの選択
from database.local_postgresql_database import endpoint

# tracemallocを有効にする
import tracemalloc
tracemalloc.start()

error_token_expired = "有効期限が切れています。再登録をしてください。"
error_access_denied = "アクセス権限がありません。"
error_forbidden_second_order = "きょう２度目の注文です。重複注文により注文できません。\nそのままブラウザを閉じてください。"
error_login_failure = "ログインに失敗しました。"
error_illegal_cookie = "Cookieの取得に失敗しました。"
error_unexpected_error_message = "予期しないエラーが発生しました。"
error_database_access = "データベース接続に失敗しました。時間をおいて再試行してください。"

# -----------------------------------------------------
import jwt
from core.security import decode_jwt_token
from utils.helper import redirect_login_failure, redirect_login_success
from utils.utils import delete_all_cookies
from models.admin import init_database

# エントリポイント
@app.get("/", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def root(request: Request, response: Response):

    try:
        logger.info(f"root() - ルートにアクセスしました")
        # テストデータ作成
        await init_database() # 昨日の二重注文禁止が有効か確認する
        # print("このappはBackend versionです。")

        # 二重注文の禁止
        result , last_order = await check_permission_and_stop_order(request, response)
        logger.info(f"last_order: {last_order}")
        if result:
            return templates.TemplateResponse(
                "duplicate_order.html",
                {
                    "request": request,
                    "forbid_second_order_message": error_forbidden_second_order,
                    "last_order": last_order,
                    "endpoint": endpoint
                }
            )

        # cookies チェック
        token = request.cookies.get("token")
        if token is None:
            ''' 備考：ここは例外に置き換えない。login.htmlへリダイレクトする。
                理由：画面が停止するため
            raise TokenExpiredException("check_cookie_token()")
            '''
            logger.debug("token: ありません")
            return redirect_login_success(request, message="ようこそ")

        # token チェック
        expires = get_token_expires(request)

        if compare_expire_date(expires):
            # expires 無効
            logger.debug("token is expired.")
            return redirect_login_success(request, error=error_token_expired)
        else:
            logger.debug("token is not expired.") # expires 有効

        payload = decode_jwt_token(token) # token 解読

        username = payload['sub']
        permission = payload['permission']
        main_url = await get_main_url(permission)

        return await create_auth_response(
            username, permission, main_url)

    except ConnectionError as e:
        return redirect_error(request, error_database_access, e)
    except jwt.ExpiredSignatureError as e:
        return redirect_login_failure(request, f"トークンの有効期限が切れています", e)
    except jwt.MissingRequiredClaimError:
        return redirect_login_failure(request, f"トークンに必要なクレームが不足しています", e)
    except jwt.DecodeError as e:
        return redirect_login_failure(request, f"トークンのデコードエラー", e)
    except jwt.InvalidTokenError as e:
        return redirect_login_failure(request, f"無効なトークン", e)
    except CookieException as e:
         redirect_login_failure(request, error_illegal_cookie, e)
    except HTTPException as e:
        return redirect_login_failure(request, e.detail)
    except Exception as e:
        content_type = request.headers.get('Content-Type')
        print(f"Content-Type: {content_type}")
        if content_type == "application/json":
            json_data = await request.json()
            return redirect_login_failure(request, json_data, e)
        else:
            return redirect_login_failure(request, f"予期しないエラー", e)


# ログイン画面を表示するエンドポイント
@app.get("/login", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def login_get(request: Request):
    try:
        pass
        return redirect_login_success(request)

    except ConnectionError as e:
        return redirect_error(request, error_database_access, e)
    except DatabaseError as e:
        return redirect_login_failure(request, error="データベース異常")
    except Exception as e:
        return redirect_login_failure(
            request, error_login_failure, e)


from core.security import authenticate_user, get_user


# ログイン画面入力を受け付けるエンドポイント
''' ログインPOST '''
@app.post("/login", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def login_post(request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()):

    try:
        input_username = form_data.username
        input_password = form_data.password

        user = await get_user(input_username, input_password, "")
        user = await authenticate_user(user, input_password) 

        permission = user.get_permission()
        main_url = await get_main_url(permission)

        return await create_auth_response(
            user.get_username(), permission, main_url)

    except ConnectionError as e:
        return redirect_error(request, error_database_access, e)
    except DatabaseError as e:
        return redirect_login_failure(request, error="データベース異常")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TokenExpiredException) as e:
         return redirect_login_success(request,error=error_token_expired)
    except (CookieException, SQLException) as e:
        return redirect_login_failure(request, e.detail, e)
    except NotAuthorizedException as e:
        return redirect_login_failure(request, error=error_access_denied)    
    except HTTPException as e:
        return redirect_login_failure(request, e.detail)
    except Exception as e:
        return redirect_error(request, error_unexpected_error_message, e)



# cookieを削除してログアウト
@app.get("/clear", tags=["users"])
@log_decorator
async def clear_cookie(response: Response):
    response = RedirectResponse(url="/")

    delete_all_cookies(response)

    return response

from schemas.order_schemas import OrderUpdateList
from services.order_view import batch_update_orders

@app.post("/update_cancel_status")
async def update_cancel_status(update: OrderUpdateList):
    logger.info(f"受信内容: {update.updates}")

    return await batch_update_orders([item.model_dump() for item in update.updates])





@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    # ブラウザが要求するfaviconのエラーを防ぐ
    # https://github.com/fastapi/fastapi/discussions/11385
    favicon_path = './static/favicon.ico'  # Adjust path to file

    return FileResponse(favicon_path)
 
# Mount the directory where favicon.ico is located 
# faviconのマウント
import os
from fastapi.staticfiles import StaticFiles
static_path = os.path.join(os.path.dirname(__file__), "static")  # 絶対パスに変換
app.mount("/static", StaticFiles(directory=static_path), name="static")
# 備考：上記設定により環境変数PYTHONPATH設定は不要

# 他のモジュールでの誤使用を防ぐ
import asyncio
import sys
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


@app.get("/logs", response_class=HTMLResponse, tags=["admin"])
async def list_logs():
    # 入力例 https://127.0.0.0.1:8000/logs/2025-03-10
    # 備考　現在誰でもログにアクセスできる
    """logs フォルダ内のログファイル一覧を表示"""
    if not os.path.exists(LOGS_DIR):
        return "<h1>No logs found</h1>"

    files = sorted(os.listdir(LOGS_DIR), reverse=True)  # 最新のログを上に
    file_links = [f'<a href="/logs/{file}">{file}</a><br>' for file in files]

    return "<h1>Log Files</h1>" + "".join(file_links)

from fastapi.responses import HTMLResponse, PlainTextResponse

@app.get("/logs/{filename}", tags=["admin"])
async def read_log(filename: str):
    """指定されたログファイルの内容をHTMLで表示"""
    filepath = os.path.join(LOGS_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Log file not found")

    # 空ファイルチェック（0バイト）
    if os.path.getsize(filepath) == 0:
        return PlainTextResponse("ログファイルは空です。", status_code=204)  # または HTML 表示にする場合はHTMLResponseを使ってもOK
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f"<h1>{filename}</h1><pre>{f.read()}</pre>"

    return HTMLResponse(content)

