# routers/admin.py
# ../admin/meになる
'''
    1. admin_view(request: Request): 
    2. update_existing_passwords():

    3. test_exception(request: Request):

    4. admin_logs_redirect():
    5. admin_order_logs_redirect():
'''
import bcrypt
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models.user import update_user, select_all_users

from utils.helper import redirect_error, redirect_unauthorized
from utils.utils import log_decorator
from utils.permission_helper import check_permission

templates = Jinja2Templates(directory="templates")

# admin_router = APIRouter()
admin_router = APIRouter(tags=["admin"])


from database.local_postgresql_database import endpoint

from venv import logger

from models.user import select_user
# 管理者画面
# 注意：エンドポイントにprefix:adminはつけない
@admin_router.get(
    "/me",
    summary="メイン画面：管理者ユーザー",
    description="",
    response_class=HTMLResponse,
    tags=["admin"]
)
@log_decorator
async def admin_view(request: Request):    
    try:
        if not (await check_permission(request, [99])):
            return redirect_unauthorized(request, "管理者権限がありません。")

        # ✅ Cookieからログイン中のユーザーを取得
        cookies = request.cookies
        username = cookies.get("sub")
        user = await select_user(username)

    except Exception as e:
        message = f"admin_view() - 予期せぬエラーが発生しました: {str(e)}"
        return await redirect_error(request, message, e)
    else:
        return templates.TemplateResponse(
            "admin.html", {
                "request": request,
                "base_url": endpoint,
                "user": user 
            }
        )

@log_decorator
@admin_router.get(
    "/me/update_existing_passwords",
    summary="ユーザーパスワードの暗号化：管理者ユーザー",
    description="すべてのユーザーパスワードの暗号化する。",
    response_class=HTMLResponse,
    tags=["admin"])
async def update_existing_passwords(request: Request):
    """既存ユーザーの全パスワードをハッシュ化"""
    from utils.helper import redirect_login_success
    try:
        users = await select_all_users()  # すべてのユーザーを取得する関数が必要
        for user in users:
            if not user.get_password().startswith("$2b$"):  # bcryptのハッシュでない場合

                """パスワードをハッシュ化する"""
                salt = bcrypt.gensalt()
                password = user.get_password()
                hashed_password = bcrypt.hashpw(password.encode(), salt)
                new_hashed_password = hashed_password.decode()  # バイト列を文字列に変換

                await update_user(
                    user.username, "password", new_hashed_password)  # DB更新

    except Exception as e:
        message = f"update_existing_passwords() - 予期せぬエラーが発生しました"
        return await redirect_error(request, message, e)
    else:
        return redirect_login_success(request, f"ユーザー {user.username} のパスワードをハッシュ化しました")

'''
# 例外テスト
# 備考：例外ハンドラとこれをmain.py以外に移動すると、JSON表示のみになる。
'''
@admin_router.get(
    "/test_exception",
    summary="テスト例外発生：管理者ユーザー",
    description="管理者画面でテスト例外を発生する。",
    tags=["admin"]
)
async def test_exception(request: Request):
    # raise CustomException(400, "test_exception()", "これはテストエラーです")
    logger.exception("管理者によるテスト例外")
    return await redirect_error(request, "管理者によりテスト例外がraiseされました")


from fastapi.responses import RedirectResponse

# logsディレクトリ内のファイル一覧を取得
# logsページへリダイレクト
@admin_router.get(
    "/logs",
    summary="ログ表示画面：管理者ユーザー",
    description="管理者画面のログタブで、一般ログを表示する。",
    include_in_schema=False,
)
async def admin_logs_redirect(request: Request):
    if not (await check_permission(request, [99])):
            return redirect_unauthorized(request, "管理者権限がありません。")
    return RedirectResponse(url="/api/v1/log_html")


# order_logsページへリダイレクト
@admin_router.get(
    "/order_logs",
    summary="注文ログ表示画面：管理者ユーザー",
    description="管理者画面のログタブで、すべての注文ログを表示する。",
    include_in_schema=False)
async def admin_order_logs_redirect(request: Request):
    if not (await check_permission(request, [99])):
            return redirect_unauthorized(request, "管理者権限がありません。")
    return RedirectResponse(url="/api/v1/order_log_html")

