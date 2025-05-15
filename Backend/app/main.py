# Backend/app/main.py
# 2.3 システムテスト完了
'''ページ・ビュー・関数
    1. root(request: Request, response: Response):
    2. login_get(request: Request):
    3. login_post(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):

    4. clear_cookie(response: Response):

    5. class CancelUpdate(BaseModel):
        updates: List[dict]  # 各辞書は {"order_id": int, "checked": bool} の形式
    6. update_cancel_status(update: CancelUpdate):

    7. custom_exception_handler(request: Request, exc: CustomException):
    8. test_exception():

    9. favicon():
    10. list_logs():
    11. read_log(filename: str):
'''
from fastapi import Depends, FastAPI, Response, HTTPException, Request, requests, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound

from utils.helper import create_auth_response, get_main_url, redirect_error
from utils.utils import *
from sqlalchemy.exc import DatabaseError
from log_unified import logger

from routers.router import sample_router
from routers.admin import admin_router
from routers.manager import manager_router
from routers.shop import shop_router
from routers.user import user_router

app = FastAPI()
templates = Jinja2Templates(directory="templates")


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


# エントリポイントの選択
from database.local_postgresql_database import endpoint

# tracemallocを有効にする
import tracemalloc
tracemalloc.start()


from core.constants import (
    ERROR_TOKEN_EXPIRED,
    ERROR_ACCESS_DENIED,
    ERROR_LOGIN_FAILURE,
    ERROR_UNEXPECTED_ERROR_MESSAGE,
    ERROR_DATABASE_ACCESS
)
# -----------------------------------------------------
import jwt
from core.security import decode_jwt_token
from utils.helper import redirect_login_failure, redirect_login_success
from utils.utils import delete_all_cookies, check_order_duplex
from models.admin import init_database
from requests.exceptions import ConnectionError
import requests

# エントリポイント
@app.get("/", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def root(request: Request):

    try:
        logger.info(f"root() - ルートにアクセスしました")
        # テストデータ作成
        # await init_database() # 昨日の二重注文禁止が有効か確認する
        # print("このappはBackend versionです。")


        # ここでCookieよりuserの有無をチェックする
        username = request.cookies.get("sub") # ログオフしたら再注文できる　それと登録なしユーザーも返却値が発生する。

        if not username:
            # ログを出して処理を止める
            logger.info("Cookieから username が取得できませんでした。")
            return RedirectResponse(url="/login?message=ログインしてください。", status_code=303)

        # 二重注文の禁止
        has_order, response = await check_order_duplex(request)
        if has_order:
            return response


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
            return redirect_login_success(request, error=ERROR_TOKEN_EXPIRED)
        else:
            logger.debug("token is not expired.") # expires 有効

        payload = decode_jwt_token(token) # token 解読

        username = payload['sub']
        permission = payload['permission']
        main_url = await get_main_url(permission)

        return await create_auth_response(
            username, permission, main_url)


    # トークン検証に失敗した場合の例外
    except jwt.ExpiredSignatureError:
        return redirect_login_failure(request, "トークンの有効期限が切れています")
    except jwt.MissingRequiredClaimError:
        return redirect_login_failure(request, "トークンに必要なクレームが不足しています")
    except jwt.DecodeError:
        return redirect_login_failure(request, "トークンの形式が不正です")
    except jwt.InvalidTokenError:
        return redirect_login_failure(request, "無効なトークンです")

    # 特に、トークン検証前後に「外部認証サーバ」「外部API」「DBアクセス」 などが関わる場合、
    # 接続系のエラー（ConnectionError）も考慮すべきです。
    except requests.exceptions.ConnectionError as ce:
        logger.exception("外部認証サーバへの接続に失敗しました")
        return await redirect_error(request, "認証サーバに接続できませんでした", ce)

    except ConnectionError as ce:
        logger.exception("ネットワーク接続エラーが発生しました")
        return await redirect_error(request, "ネットワーク接続に失敗しました", ce)

    # check_permission_and_stop_orderから投げている
    except HTTPException as e:
        logger.exception(f"HTTPException 発生 - ステータス: {e.status_code}, 内容: {e.detail}")
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            return redirect_login_failure(request, e.detail)
        elif e.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return await redirect_error(request, "内部サーバーエラーが発生しました", e)
        else:
            return await redirect_error(request, "不明なHTTPエラーが発生しました", e)

    except Exception as e:
        logger.exception("root() - 予期せぬエラーが発生しました")
        return redirect_login_failure(request, f"予期せぬエラーが発生しました: {str(e)}", e)


# 新規登録画面
@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# 重複ユーザーの有無確認
async def is_user_exists(username: str) -> bool:
    existing_user = await select_user(username)
    return existing_user is not None

# 新規登録画面
@app.post("/register", response_class=HTMLResponse)
@log_decorator
async def register_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    nickname: str = Form(...)
):
    try:
        logger.info(f"/register - 登録処理開始: {username}")

        # ここで重複ユーザー確認
        if await is_user_exists(username):
            logger.warning(f"/register - 既存ユーザー名: {username}")
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "重複するIDです。別のIDを入力してください。"},
                status_code=400
            )

        # ユーザー取得・登録
        user = await get_user(username, password, nickname)
        if user is None:
            logger.warning(f"/register - ユーザー取得に失敗: {username}")
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "ユーザー登録に失敗しました。もう一度お試しください。"},
                status_code=400
            )

        nick_name = user.get_name()
        logger.info(f"/register - 登録成功: {username}（{nick_name}）")

        # 成功メッセージとリダイレクト
        return redirect_login_success(request, f"ユーザー登録が完了しました。{nick_name}さん、ログインしてください。")

    except HTTPException as e:
        logger.exception(f"/register - HTTPException: {e.detail}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"HTTPエラー: {e.detail}"},
            status_code=e.status_code
        )

    except Exception as e:
        logger.exception("/register - 予期せぬエラーが発生")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "予期せぬエラーが発生しました。しばらくしてからお試しください。"},
            status_code=500
        )


# ログイン画面を表示するエンドポイント
@app.get("/login", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def login_get(request: Request):
    try:
        has_order, response = await check_order_duplex(request)
        if has_order:
            return response
        
        
        # ログイン成功画面にリダイレクト
        return redirect_login_success(request)

    except ConnectionError as e:
        logger.exception("データベースまたは外部接続失敗")
        return await redirect_error(request, ERROR_DATABASE_ACCESS, e)

    except TemplateNotFound as e:
        logger.exception("テンプレート login.html が見つかりません")
        return await redirect_error(request, "ログイン画面が利用できません。", e)

    except (AttributeError, TypeError) as e:
        logger.exception("リクエストオブジェクトが不正")
        return await redirect_login_failure(request, error="リクエストデータが不正です。")

    # 将来的にユーザー情報取得やDBアクセスを追加した場合に備え、
    # DatabaseError ハンドリングをここに追加することを検討
    
    except HTTPException as e:
        logger.exception(f"HTTPException 発生 - ステータス: {e.status_code}, 内容: {e.detail}")
        return await redirect_login_failure(request, e.detail)

    except Exception as e:
        logger.exception("予期せぬエラーが発生しました")
        return await redirect_login_failure(request, ERROR_LOGIN_FAILURE, e)


from core.security import authenticate_user, get_user
from sqlalchemy.exc import SQLAlchemyError

# ログイン画面入力を受け付けるエンドポイント
''' ログインPOST '''
@app.post("/login", response_class=HTMLResponse, tags=["users"])
@log_decorator
async def login_post(request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()):

    try:
        input_username = form_data.username
        input_password = form_data.password

        # # 二重注文の拒否
        # has_order, response = await check_order_duplex(request)
        # if has_order:
        #     return response

        # ユーザー取得・認証
        user = await get_user(input_username, input_password, "")
        user = await authenticate_user(user, input_password) 
        if user is None:
            logger.warning(f"ユーザー認証に失敗しました: {input_username}")
            # ここでパスワード間違いのメッセージを表示
            return redirect_login_failure(request, error="パスワードが間違っています")

        # ここで認証成功後に username をセットして判定させる
        request._cookies["sub"] = user.get_username()  # Cookieをセットするか、別途パラメータとして渡す

        # 二重注文の拒否
        has_order, response = await check_order_duplex(request)
        if has_order:
            return response

        # 権限確認
        permission = user.get_permission()
        main_url = await get_main_url(permission)

        return await create_auth_response(
            user.get_username(), permission, main_url)

    except ConnectionError as e:
        logger.exception("DBまたは外部接続失敗")
        return await redirect_error(request, ERROR_DATABASE_ACCESS, e)

    except (DatabaseError, SQLAlchemyError) as e:
        logger.exception("データベース操作失敗")
        return redirect_login_failure(request, error="データベース異常")
        
    except HTTPException as e:
        logger.exception(f"HTTPException 発生 - ステータス: {e.status_code}, 内容: {e.detail}")
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            return redirect_login_failure(request, e.detail)
        elif e.status_code == status.HTTP_403_FORBIDDEN:
            return redirect_login_failure(request, error=ERROR_ACCESS_DENIED)
        elif e.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return await redirect_error(request, e.detail, e)
        else:
            return await redirect_error(request, "不明なHTTPエラーが発生しました", e)

    except Exception as e:
        logger.exception("予期せぬエラーが発生しました")
        return await redirect_error(request, ERROR_UNEXPECTED_ERROR_MESSAGE, e)



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

# for route in app.routes:
#     print(route.path, route.name)