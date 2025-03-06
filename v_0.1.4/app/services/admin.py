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
        raise CustomException(status.HTTP_401_UNAUTHORIZED, "check_admin_permission()", f"Not Authorized permission={permission}")

# 管理者画面
# 注意：エンドポイントにprefix:adminはつけない
@admin_router.get("/today", response_class=HTMLResponse)
@log_decorator
def admin_view(request: Request):    
    
    # 権限チェック
    check_admin_permission(request)
    
    return templates.TemplateResponse(
        "admin.html", {"request": request})

# 例外テスト
@admin_router.get("/test_exception")
async def test_exception():
    raise CustomException(400, "test_exception()", "これはテストエラーです")