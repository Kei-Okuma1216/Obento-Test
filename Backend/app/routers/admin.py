# routers/admin.py
# ../admin/meになる
'''
    1. admin_view(request: Request): 
    2. update_existing_passwords():
    3. get_admin_orders(begin: str):

    4. list_logs():
    5. view_log(filename: str):
    6. list_order_logs():
    7. view_order_log(filename: str):
'''
import bcrypt
import os
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models.user import update_user, select_all_users

from utils.helper import redirect_error, redirect_unauthorized
from utils.utils import check_permission, log_decorator

templates = Jinja2Templates(directory="templates")

admin_router = APIRouter()


from database.local_postgresql_database import endpoint

from venv import logger

# 管理者画面
# 注意：エンドポイントにprefix:adminはつけない
@admin_router.get("/me", response_class=HTMLResponse, tags=["admin"])
@log_decorator
async def admin_view(request: Request):    
    try:
        if not (await check_permission(request, [99])):
            return redirect_unauthorized(request, "管理者権限がありません。")

    except Exception as e:
        message = f"admin_view() - 予期せぬエラーが発生しました: {str(e)}"
        return await redirect_error(request, message, e)
    else:
        return templates.TemplateResponse(
            "admin.html", {
                "request": request,
                "base_url": endpoint
            }
        )

@log_decorator
@admin_router.get("/me/update_existing_passwords", response_class=HTMLResponse, tags=["admin"])
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


from fastapi.responses import JSONResponse
from datetime import datetime
from models.order import select_orders_by_admin_at_date


# 注文ログファイルの内容JSONを表示するエンドポイント
@admin_router.get("/orders/admin", tags=["admin"])
async def get_admin_orders(begin: str):
    """
    管理者用 注文JSON取得API
    パラメータ begin は yyyy-mm-dd 形式の日付文字列
    """
    try:
        if not begin:
            return JSONResponse({"error": "開始日が指定されていません"}, status_code=400)

        try:
            target_date = datetime.strptime(begin, "%Y-%m-%d").date()
        except ValueError:
            return JSONResponse({"error": "開始日フォーマットが不正です (yyyy-mm-dd 形式)"}, status_code=400)

        # 管理者用の注文取得関数を呼び出し
        orders = await select_orders_by_admin_at_date(target_date)

        if not orders:
            return JSONResponse({"message": "注文が見つかりません"}, status_code=404)

        # Pydanticモデルから辞書リストに変換
        orders_json = [order.model_dump() for order in orders]

        return JSONResponse(content=orders_json, media_type="application/json; charset=utf-8")

    except Exception as e:
        return JSONResponse({"error": f"サーバーエラー: {str(e)}"}, status_code=500)


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
'''
@admin_router.get("/test_exception")
async def test_exception(request: Request):
    # raise CustomException(400, "test_exception()", "これはテストエラーです")
    logger.exception("管理者によるテスト例外")
    return await redirect_error(request, "管理者によりテスト例外がraiseされました")

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


from fastapi import HTTPException
# 注文ログファイルの内容を表示するエンドポイント
@admin_router.get("/order_logs/{filename}", response_class=HTMLResponse, tags=["admin", "shops"])
def view_order_log(filename: str):
    log_path = os.path.join("order_logs", filename)
    
    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read().replace('\n', '<br>')
            return f"<h1>{filename}</h1><pre>{content}</pre>"
        else:
            logger.warning(f"注文ログファイルが見つかりません: {filename}")
            return HTMLResponse("注文ログファイルが存在しません。", status_code=404)

    except ConnectionResetError:
        logger.warning(f"クライアントが接続を切断しました（ログ読み込み中: {filename}）")
        return HTMLResponse("接続が中断されました。", status_code=499)

    except Exception as e:
        logger.error(f"注文ログの読み込みエラー（{filename}）: {e}")
        raise HTTPException(status_code=500, detail="ログファイルの読み込み中にエラーが発生しました")

