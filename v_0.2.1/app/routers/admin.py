# admin.py
# ../admin/meになる
'''
    1. admin_view(request: Request): 
    2. update_existing_passwords():

    3. list_logs():
    4. view_log(filename: str):
    5. list_order_logs():
    6. view_order_log(filename: str):
'''
import bcrypt
import os
from fastapi import Request, APIRouter, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
#from database.sqlite_database import update_user, get_all_users
from database.user import update_user, select_all_users

from utils.exception import CustomException, NotAuthorizedException
from helper import redirect_login
from utils.utils import check_permission, log_decorator

templates = Jinja2Templates(directory="templates")

admin_router = APIRouter()


from database.sqlalchemy_database import endpoint

from venv import logger

# 管理者画面
# 注意：エンドポイントにprefix:adminはつけない
@admin_router.get("/me", response_class=HTMLResponse, tags=["admin"])
@log_decorator
def admin_view(request: Request):    
    try:
        if not(check_permission(request, ["99"])):
            raise NotAuthorizedException("管理者権限がありません。")

        return templates.TemplateResponse(
            "admin.html", {
                "request": request,
                "base_url": endpoint})

    except NotAuthorizedException as e:
        return redirect_login(request, "アクセス権限がありません。", e)
    except Exception as e:
        raise CustomException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "/admin_view()",
            f"予期せぬエラーが発生しました: {str(e)}")

@log_decorator
@admin_router.get("/me/update_existing_passwords", response_class=HTMLResponse, tags=["admin"])
async def update_existing_passwords():
    """既存ユーザーのパスワードをハッシュ化"""
    users = await select_all_users()  # すべてのユーザーを取得する関数が必要
    for user in users:
        if not user.get_password().startswith("$2b$"):  # bcryptのハッシュでない場合

            """パスワードをハッシュ化する"""
            salt = bcrypt.gensalt()
            password = user.get_password()
            hashed_password = bcrypt.hashpw(password.encode(), salt)
            new_hashed_password = hashed_password.decode()  # バイト列を文字列に変換
            #new_hashed_password = hash_password(user.get_password())  # ハッシュ化

            await update_user(
                user.username, "password", new_hashed_password)  # DB更新
            logger.info(f"ユーザー {user.username} のパスワードをハッシュ化しました")


'''
# 注意：ここに移動するとJSONのみ表示になる
# 例外ハンドラーの設定
# 実装例
# raise CustomException(400, "token の有効期限が切れています。再登録をしてください。")
@admin_router.exception_handler(CustomException)
async def custom_exception_handler(
    request: Request, exc: CustomException):
    print(f"例外ハンドラーが呼ばれました: {exc.detail}")  # デバッグ用
    """カスタム例外をキャッチして、HTML にエラーを表示"""
    return templates.TemplateResponse(
        "error.html",  # templates/error.html を表示
        {"request": request, "message": exc.detail["message"], "status_code": exc.status_code},
        status_code=exc.status_code
    )

# 例外テスト
# 備考：例外ハンドラとこれをmain.py以外に移動すると、JSON表示のみになる。
@admin_router.get("/test_exception")
async def test_exception():
    raise CustomException(400, "test_exception()", "これはテストエラーです")
'''
# logsディレクトリ内のファイル一覧を取得
@admin_router.get("/logs", response_class=HTMLResponse, tags=["admin"])
def list_logs():

    log_dir = "logs"
    if not os.path.exists(log_dir):
        return "<h1>ログディレクトリが存在しません</h1>"
    log_files = sorted(os.listdir(log_dir), reverse=True)
    # 各ログファイルへのリンクを作成
    links = [f"<li><a href='/admin/logs/{file}'>{file}</a></li>" for file in log_files]
    
    return f"<h1>ログ一覧</h1><ul>{''.join(links)}</ul>"

# ログファイル表示
@admin_router.get("/logs/{filename}", response_class=HTMLResponse, tags=["admin"])
def view_log(filename: str):
    log_path = os.path.join("logs", filename)
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            # 改行を<br>に置換してHTML上で見やすく表示
            content = f.read().replace('\n', '<br>')
        return f"<h1>{filename}</h1><pre>{content}</pre>"
    else:
        return "ログファイルが存在しません。"

# 注文ログファイル一覧を表示するエンドポイント
@admin_router.get("/order_logs", response_class=HTMLResponse, tags=["admin","shops"])
def list_order_logs():
    log_dir = "order_logs"  # order_log_config.py と同じディレクトリ名
    if not os.path.exists(log_dir):
        return "<h1>注文ログディレクトリが存在しません</h1>"
    log_files = sorted(os.listdir(log_dir), reverse=True)
    links = [f"<li><a href='/admin/order_logs/{file}'>{file}</a></li>" for file in log_files]
    return f"<h1>注文ログ一覧</h1><ul>{''.join(links)}</ul>"

# 注文ログファイルの内容を表示するエンドポイント
@admin_router.get("/order_logs/{filename}", response_class=HTMLResponse, tags=["admin","shops"])
def view_order_log(filename: str):
    log_path = os.path.join("order_logs", filename)
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read().replace('\n', '<br>')
        return f"<h1>{filename}</h1><pre>{content}</pre>"
    else:
        return "注文ログファイルが存在しません。"

