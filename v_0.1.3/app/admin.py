# 管理者の権限チェック
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")
from fastapi.staticfiles import StaticFiles
from utils import log_decorator
from fastapi import APIRouter

admin_router = APIRouter()

@log_decorator
def check_admin_permission(request: Request):
    permission = request.cookies.get("permission")
    print(f"permission: {permission}")
    if permission != "99":
        raise HTTPException(status_code=403, detail="Not Authorized")

# 管理者画面
# 注意：エンドポイントにprefix:adminはつけない
@admin_router.get("/today", response_class=HTMLResponse)
@log_decorator
def admin_view(request: Request):    
    
    # 権限チェック
    check_admin_permission(request)
    
    return templates.TemplateResponse(
        "admin.html", {"request": request})