# Backend/app/main.py
# 3.3 二重注文禁止画面から注文履歴画面まで遷移できる
'''ページ・ビュー・関数
    1. root(request: Request, response: Response):

    2. register_get(request: Request):
    3. is_user_exists(username: str) -> bool:
    4. register_post(request: Request, username: str = Form(...), password: str = Form(...), nickname: str = Form(...)):

    5. login_get(request: Request):
    6. login_post(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):

    7. clear_cookie(response: Response):
    8. logout():

    9. update_check_status(update: CancelUpdate):
    10. favicon():
    11. debug_routes():

    12. cancel_root(request: Request):
'''
from fastapi import Depends, FastAPI, Response, HTTPException, Request, requests, Form, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound

from utils.helper import create_auth_response, get_main_url, redirect_error
from utils.decorator import log_decorator

from sqlalchemy.exc import DatabaseError
from log_unified import logger, log_order

# サーバ起動時のみ初期化する
from contextlib import asynccontextmanager
from models.admin import init_database

# app未使用の警告はエディタの静的解析によるもので、FastAPIでは問題ありません。
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # テストデータ作成
    # await init_database() # コメントアウトしないと、毎回データを初期化する。
    print("このappはBackend versionです。ローカル環境のDockerコンテナで実行してください。")
    await init_database()
    yield

app = FastAPI(lifespan=lifespan)
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

from routers.router import account_router
from routers.admin import admin_router
from routers.manager import manager_router
from routers.shop import shop_router
from routers.user import user_router
from routers.order import order_api_router
from routers.log import log_router

# UI表示系（HTMLを返す） → prefixなしで短く、直感的に
app.include_router(admin_router, prefix="/admin")
app.include_router(manager_router, prefix="/manager")
app.include_router(shop_router)
app.include_router(user_router, prefix="/user")
# API専用系（JSONを返す） → prefix付きで明示的に
app.include_router(account_router, prefix="/api")
app.include_router(order_api_router)
# app.include_router(order_api_router, prefix="/api/v1/order")　＃これで表示されていないので保留にしている。
app.include_router(log_router)

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
import requests
from requests.exceptions import ConnectionError

from core.security import decode_jwt_token
from models.admin import init_database
from utils.helper import redirect_login_failure, redirect_login_success
from utils.cookie_helper import get_token_expires, compare_expire_date, delete_all_cookies
from utils.permission_helper import get_last_order_simple


'''
備考
 接続先変更する場合は、あらかじめ core\settings.pyを変更してください。
問題点
 現在ログオフしたら再注文できる。登録なしユーザーも返却値が発生する。
'''
# エントリポイント
@app.get("/",
         response_class=HTMLResponse,
         summary="アプリケーションのエントリポイント",
         description="ユーザーはCookieにusernameがあればcreate_auth_responseで権限別のページへ遷移する。途中一般ユーザーは二重注文のチェックが入る。",
         tags=["login"])
# @log_decorator
async def root(request: Request):
    try:
        logger.info(f"root() - ルートにアクセスしました")

        username = request.cookies.get("sub")
        if not username:
            logger.debug("Cookieから username が取得できませんでした。")
            logger.info("ログイン画面を表示します。")
            return RedirectResponse(url="/login?message=ログインしてください。", status_code=303)

        token = request.cookies.get("token")
        if token is None:
            ''' 備考：ここは例外に置き換えない。login.htmlへリダイレクトする。
                理由：画面が停止するため
            raise TokenExpiredException("check_cookie_token()")ダメ！
            '''
            logger.debug("token: ありません")
            return redirect_login_success(request, message="ようこそ")

        expires = get_token_expires(request)
        if compare_expire_date(expires):
            logger.debug("token is expired.")# expires 無効
            return redirect_login_success(request, error=ERROR_TOKEN_EXPIRED)
        else:
            logger.debug("token is not expired.") # expires 有効


        payload = decode_jwt_token(token) # token 解読
        username = payload['sub']
        permission = payload['permission']

        # 一般ユーザー（permission == 1）の場合のみ二重注文チェック
        if str(permission) == "1":
            logger.info(f"一般ユーザーの二重注文チェック開始 - username: {username}")

            # JWTから取得したusernameでリクエストCookieを更新
            request._cookies["sub"] = username

            response = await get_last_order_simple(request)
            if response:
                logger.warning(f"当日二重注文が検出されました。username: {username}")
                return response
            else:
                logger.info(f"二重注文なし。処理を続行します。username: {username}")

        user = await get_user(username)
        if user is None:
            return redirect_login_failure(request, error="ユーザー情報が取得できません。")


        kwargs = {}
        if str(permission) == "1":
            kwargs["user_id"] = str(user.get_id())
        elif str(permission) == "2":
            kwargs["manager_id"] = user.get_id()
        elif str(permission) == "10":
            kwargs["shop_id"] = user.get_id()

        main_url = await get_main_url(permission, **kwargs)
        logger.debug(f"get_main_url() 戻り値 - main_url: {main_url}")

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
@app.get(
    "/register",
    summary="ユーザー新規登録画面（入力前）",
    description="画面表示のみ",
    response_class=HTMLResponse,
    tags=["login"]
    )
async def register_get(request: Request):
    logger.info("/register - 新規登録画面にアクセスしました")
    return templates.TemplateResponse(
        "register.html", {"request": request})

# 重複ユーザーの有無確認
from models.user import select_user
async def is_user_exists(username: str) -> bool:
    existing_user = await select_user(username)
    print(f"existing_user: {existing_user}")
    return existing_user is not None

from utils.helper import redirect_register
from models.user import register_or_get_user

# 新規登録画面
@app.post(
    "/register",
    summary="ユーザー新規登録画面（入力後）",
    description="既存ユーザーを確認して、重複がなければ登録。その後リダイレクトする。",
    response_class=HTMLResponse,
    tags=["login"]
)
@log_decorator
async def register_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    nickname: str = Form(...)
):
    try:
        logger.info(f"/register - 登録処理開始: {username}")

        # 既存ユーザー確認（is_user_exists は取得専用）
        if await is_user_exists(username):
            return redirect_register(request, username, "ユーザー名が重複しています。")

        # ユーザー登録 or 取得（登録後取得できなければエラーにする）
        user = await register_or_get_user(username, password, nickname)
        if user is None: 
            return redirect_register(request, username, "ユーザー登録に失敗しました。もう一度お試しください。")

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
@app.get(
    "/login",
    summary="ログイン画面（入力前）",
    description="二重注文をチェック後、リダイレクトする。",
    response_class=HTMLResponse,
    tags=["login"]
)
@log_decorator
async def login_get(request: Request):
    try:
        # 二重注文チェックを削除（ログイン前なので不要）
        return templates.TemplateResponse("login.html", {"request": request, "message": None, "error": None})

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


from core.security import authenticate_user
from models.user import get_user
from sqlalchemy.exc import SQLAlchemyError

# ログイン画面入力を受け付けるエンドポイント
''' ログインPOST '''
@app.post(
    "/login",
    summary="ログイン画面（入力後）",
    description="ユーザー認証と二重注文をチェック後、ユーザーメイン画面にリダイレクトする。",
    response_class=HTMLResponse,
    tags=["login"])
@log_decorator
async def login_post(request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()):

    try:
        input_username = form_data.username
        input_password = form_data.password
        logger.info(f"login_post() - ユーザー認証開始: {input_username}")

        # ユーザー取得・認証
        user = await get_user(input_username)
        if user is None:
            logger.warning(f"ユーザーが存在しません: {input_username}")
            return redirect_login_failure(request, error="ユーザーが存在しません")

        user = await authenticate_user(user, input_password) 
        if user is None:
            logger.warning(f"ユーザー認証に失敗しました: {input_username}")
            return redirect_login_failure(request, error="パスワードが間違っています")

        # ここで認証成功後に username をセットして判定させる
        logger.info(f"ユーザー認証成功: {input_username}（{user.get_name()}）")
        request._cookies["sub"] = user.get_username()  # Cookieをセットするか、別途パラメータとして渡す

        # 一般ユーザー（permission == 1）の場合のみ二重注文チェック
        user_permission = user.get_permission()
        username = user.get_username()
        if str(user_permission) == "1":
            logger.info(f"一般ユーザーの二重注文チェック開始 - username: {username}")

            response = await get_last_order_simple(request)
            if response:
                logger.warning(f"当日二重注文が検出されました。username: {username}")
                return response
            else:
                logger.info(f"二重注文なし。処理を続行します。username: {username}")



        # 権限確認
        permission = user.get_permission()
        kwargs = {}
        if str(permission) == "1":
            kwargs["user_id"] = str(user.get_id())
        elif str(permission) == "2":
            kwargs["manager_id"] = user.get_id()
        elif str(permission) == "10":
            kwargs["shop_id"] = user.get_id()

        main_url = await get_main_url(permission, **kwargs)
        logger.debug(f"get_main_url() 戻り値 - main_url: {main_url}")

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

    else:
        return await create_auth_response(user.get_username(), permission, main_url)


# cookieを削除してログアウト
@app.get(
    "/clear",
    summary="Cookieをクリアする",
    description="Cookieクリアにより強制的にログアウト状態になる。",
    tags=["login"]
)
@log_decorator
async def clear_cookie(response: Response):
    # /clear で cookie を削除しているが、response: Response 引数の上書きで削除が効いていない
    # または、リダイレクト先 / が再度クッキー依存処理を実行してしまう設計の問題
    # response = RedirectResponse(url="/")
    response = RedirectResponse(url="/login")

    delete_all_cookies(response)

    return response

from fastapi.responses import RedirectResponse

@app.get(
    "/logout",
    summary="ログアウト",
    tags=["login"]
)
@log_decorator
def logout():
    response = RedirectResponse(url="/login")
    delete_all_cookies(response)
    return response


from schemas.order_schemas import OrderUpdateList
from services.order_view import batch_update_orders

@app.post(
    "/update_check_status",
    summary="チェックボックス更新",
    description="注文テーブルのチェックボックス更新する。",
    tags=["util"]
)
@log_decorator
async def update_check_status(update: OrderUpdateList):
    logger.info(f"受信内容: {update.updates}")

    return await batch_update_orders([item.model_dump() for item in update.updates])




@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    # ブラウザが要求するfaviconのエラーを防ぐ
    # https://github.com/fastapi/fastapi/discussions/11385
    favicon_path = './static/images/favicon.ico'  # Adjust path to file

    return FileResponse(favicon_path)
# もしくはこれで可能
# @app.get("/favicon.ico", include_in_schema=False)
# async def favicon():
#     return Response(status_code=204)  # No Content

 
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


# 現在登録しているルート一覧を表示する
# これはデバッグに有用なので絶対に消さない！
# for route in app.routes:
#     print(route.path, route.name)
# @app.get(
#     "/debug_routes",
#     tags=["shop"],
#     include_in_schema=False
# )
# async def debug_routes():
#     return [{"path": route.path, "name": route.name, "methods": list(route.methods)} for route in app.router.routes]

@app.get("/debug_routes", tags=["debug"])
async def debug_routes():
# https://localhost:8000/debug_routes
    routes_info = []
    for route in app.router.routes:
        try:
            routes_info.append({
                "path": route.path,
                "name": getattr(route, "name", "N/A"),
                "methods": list(getattr(route, "methods", [])),
            })
        except Exception as e:
            routes_info.append({
                "path": "ERROR",
                "error": str(e)
            })
    return routes_info


# 注文キャンセル エントリポイント
@app.get("/order/cancel",
         response_class=HTMLResponse,
         summary="注文キャンセルのエントリポイント",
         description="注文キャンセル用。NFCタグを読んでこのURLにアクセスする。その後Cookieの値により一般ユーザーの場合、最新の注文をキャンセル処理を実行する。",
         tags=["login: cancel"])
@log_decorator
async def cancel_root(request: Request):
    try:
        logger.info(f"cancel_root() - Cancelにアクセスしました")

        username = request.cookies.get("sub") # Cookieからユーザー名取得
        if not username:
            logger.debug("Cookieから username が取得できませんでした。")
            logger.info("ログイン画面を表示します。")
            return RedirectResponse(url="/login?message=ログインしてください。", status_code=303)

        # 14時以降は注文キャンセルを受け付けない
        from datetime import datetime, time
        current_time = datetime.now().time()
        if current_time >= time(14, 0):
            logger.info(f"14時以降は注文キャンセルを受け付けません。username:{username}")
            log_order(
                "CANCEL", f"取消不可 - username: {username} 14時以降は注文キャンセルを受け付けません。"
            )
            # return await redirect_error(request, "14時以降は注文キャンセルを受け付けません。")
            return templates.TemplateResponse(
                "stop_cancel.html",
                {
                    "request": request,
                    "status_code": 403,
                    "message": "14時以降は注文キャンセルを受け付けておりません。"
                },
                status_code=403
            )

        token = request.cookies.get("token") # token取得
        if token is None:
            logger.debug("token: ありません")
            logger.info("ログイン画面を表示します。")
            return redirect_login_success(request, message="ようこそ")

        # JWTのdecodeはエラーが起きやすいため局所的にtry-exceptで囲む
        try:
            expires = get_token_expires(request) # token 有効期限チェック
            if compare_expire_date(expires):
                logger.debug("token is expired.")
                return redirect_login_success(request, error=ERROR_TOKEN_EXPIRED)
            else:
                logger.debug("token is not expired.")

            payload = decode_jwt_token(token) # token 解読

        except jwt.ExpiredSignatureError:
            return redirect_login_failure(request, "トークンの有効期限が切れています")
        except jwt.MissingRequiredClaimError:
            return redirect_login_failure(request, "トークンに必要なクレームが不足しています")
        except jwt.DecodeError:
            return redirect_login_failure(request, "トークンの形式が不正です")
        except jwt.InvalidTokenError:
            return redirect_login_failure(request, "無効なトークンです")


        user = await get_user(username) # 認証済みユーザー取得
        if user is None:
            return redirect_login_failure(request, error="tokenからユーザー情報が取得できません。")

        permission = payload['permission'] # ユーザー権限取得

        if str(permission) != "1":
            return redirect_login_failure(request, error="この操作は一般ユーザーのみ実行できます")

    except requests.exceptions.ConnectionError as ce:
        logger.exception("外部認証サーバへの接続に失敗しました")
        return await redirect_error(request, "認証サーバに接続できませんでした", ce)

    except ConnectionError as ce:
        logger.exception("ネットワーク接続エラーが発生しました")
        return await redirect_error(request, "ネットワーク接続に失敗しました", ce)

    except HTTPException as e:
        logger.exception(f"HTTPException 発生 - ステータス: {e.status_code}, 内容: {e.detail}")
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            return redirect_login_failure(request, e.detail)
        elif e.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return await redirect_error(request, "内部サーバーエラーが発生しました", e)
        else:
            return await redirect_error(request, "不明なHTTPエラーが発生しました", e)

    except Exception as e:
            logger.exception("cancel_root() - 予期せぬエラーが発生しました")
            # return redirect_login_failure(request, f"予期せぬエラーが発生しました: {str(e)}", e)
            return templates.TemplateResponse(
                "stop_cancel.html",
                {
                    "request": request,
                    "status_code": 500,
                    "message": "キャンセル処理中にサーバーエラーが発生しました。"
                },
                status_code=500
            )
    else: # キャンセル画面へリダイレクト
        user_id = user.get_id()
        redirect_url = f"/user/{user_id}/order_cancel_complete/"
        logger.info(f"ユーザー認証成功: {username}, キャンセル画面にリダイレクト → {redirect_url}")
        return RedirectResponse(url=redirect_url, status_code=303)
