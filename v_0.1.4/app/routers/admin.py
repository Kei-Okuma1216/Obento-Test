# 管理者の権限チェック
from fastapi import Request, APIRouter, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from utils.exception import CustomException
from utils.utils import log_decorator

templates = Jinja2Templates(directory="templates")

admin_router = APIRouter()

@log_decorator
def check_admin_permission(request: Request):
    permission = request.cookies.get("permission")
    #print(f"permission: {permission}")
    if permission != "99":
        raise CustomException(
            status.HTTP_401_UNAUTHORIZED,
            "check_admin_permission()",
            f"Not Authorized permission={permission}")

# 管理者画面
# 注意：エンドポイントにprefix:adminはつけない
@admin_router.get("/me", response_class=HTMLResponse, tags=["admin"])
@log_decorator
def admin_view(request: Request):    
    
    # 権限チェック
    check_admin_permission(request)
    
    return templates.TemplateResponse(
        "admin.html", {"request": request})
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