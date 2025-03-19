# admin.py
import bcrypt
import os
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database.sqlite_database import update_user, get_all_users
from utils.exception import CustomException
from utils.utils import check_permission, log_decorator
from venv import logger

templates = Jinja2Templates(directory="templates")

admin_router = APIRouter()

# 管理者画面
# 注意：エンドポイントにprefix:adminはつけない
@admin_router.get("/me", response_class=HTMLResponse, tags=["admin"])
@log_decorator
async def admin_view(request: Request):    

    if await check_permission(request, [99]):
        return templates.TemplateResponse(
            "admin.html", {"request": request})
    else:
        return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})

@log_decorator
@admin_router.get("/me/update_existing_passwords", response_class=HTMLResponse, tags=["admin"])
async def update_existing_passwords():
    """既存ユーザーのパスワードをハッシュ化"""
    users = await get_all_users()  # すべてのユーザーを取得する関数が必要
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

@admin_router.get("/me/check_device", response_class=HTMLResponse, tags=["admin"])
async def check_device(request: Request):
    '''使い方
    #await init_database()
    value = await check_device(request)
    # JSON をテキストとして整形
    text_value = json.dumps(value, ensure_ascii=False, indent=4)
    logger.info(text_value)
    '''
    user_agent = request.headers.get("user-agent", "").lower()

    # 簡単なスマホ判定
    is_mobile = any(keyword in user_agent for keyword in ["iphone", "android", "mobile"])

    return {"user_agent": user_agent, "is_mobile": is_mobile}



@admin_router.get("/logs", response_class=HTMLResponse)
def list_logs():
    # logsディレクトリ内のファイル一覧を取得
    log_dir = "logs"
    if not os.path.exists(log_dir):
        return "<h1>ログディレクトリが存在しません</h1>"
    log_files = sorted(os.listdir(log_dir), reverse=True)
    # 各ログファイルへのリンクを作成
    links = [f"<li><a href='/admin/logs/{file}'>{file}</a></li>" for file in log_files]
    return f"<h1>ログ一覧</h1><ul>{''.join(links)}</ul>"

@admin_router.get("/logs/{filename}", response_class=HTMLResponse)
def view_log(filename: str):
    log_path = os.path.join("logs", filename)
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            # 改行を<br>に置換してHTML上で見やすく表示
            content = f.read().replace('\n', '<br>')
        return f"<h1>{filename}</h1><pre>{content}</pre>"
    else:
        return "ログファイルが存在しません。"


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