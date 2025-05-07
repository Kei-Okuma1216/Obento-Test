# utils/helper.py
# 必ずmain.pyとセットにすること
'''
    1. get_main_url(permission: int) -> str:
    2. create_auth_response(
        username: str, permission: int, redirect_url: str) -> Response:
    3. redirect_login(request: Request, message: str=None, error: str=None, e: Exception=None):
    4. redirect_login_success(request: Request, message: str = "ようこそ"):
    5. redirect_login_failure(request: Request, error: str, e: Exception = None):
    6. redirect_error(request: Request, message: str, e: Exception):
'''
from fastapi import HTTPException, Request, Response, status

from .utils import log_decorator, set_all_cookies
from .exception import NotAuthorizedException
from log_unified import logger

@log_decorator
async def get_main_url(permission: int) -> str:
    try:
        # リダイレクト先の選択 
        redirect_url = {
            1: "/users/order_complete",
            2: "/manager/me",
            10: "/shops/me",
            99: "/admin/me"}.get(permission, "/error")
        logger.debug(f"redirect_url: {redirect_url}")

        return redirect_url

    except Exception as e:
        logger.error(f"get_main_url() - Error: {e}")



from fastapi.responses import RedirectResponse
from core.security import get_access_token
@log_decorator
async def create_auth_response(
            username: str,
            permission: int,
            redirect_url: str) -> Response:
    try:
        """
        ユーザー情報を元に新しいトークンを生成し、Cookie を設定したリダイレクトレスポンスを返す。
        """
        data = {"sub": username, "permission": permission}
        access_token, expires = get_access_token(data)#get_new_token(data)
        new_data = {
            "sub": username,
            "permission": permission,
            "token": access_token,
            "expires": expires
        }
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

        set_all_cookies(response, new_data)

        return response

    except NotAuthorizedException as e:
        raise
    except Exception as e:
        logger.error(f"create_auth_response() - Error: {e}")


from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

@log_decorator
def redirect_login(
    request: Request,
    message: str=None,
    error: str=None,
    e: Exception=None):
    '''login.htmlに戻る'''
    try:
        if error:
            logger.error(f"Redirect Login - {error}")
        if message:
            logger.info(f"Redirect Login - {message}")

        return templates.TemplateResponse(
            "login.html", {
                "request": request,
                "message": message,
                "error": error})
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error("redirect_login() - Error: {e}")

# ログイン成功時のリダイレクト
# 正常系
@log_decorator
def redirect_login_success(request: Request, message: str = "ようこそ"):
    logger.info(f"Redirect Login - {message}")
    return templates.TemplateResponse(
        "login.html", {"request": request, "message": message, "error": None}
    )

# エラー時のリダイレクト
# 異常系
@log_decorator
def redirect_login_failure(request: Request, error: str, e: Exception = None):
    logger.error(f"Redirect Login - {error}")
    if e:
        detail_message = getattr(e, "detail", str(e))
        logger.error(f"Error detail: {detail_message}")

    return templates.TemplateResponse(
        "login.html", {"request": request, "message": None, "error": error}
    )



from fastapi import HTTPException

@log_decorator
async def redirect_error(request: Request, message: str, e: Exception = None):
    '''error.html にリダイレクトし、クエリにエラー内容を表示
        例：
        return await redirect_error(request, "アクセス権限がありません。", e)
    '''
    try:
        # 例外詳細をログ出力
        detail_message = getattr(e, "detail", None)
        
        if detail_message:
            logger.error(f"{message} - detail: {detail_message.get('message', str(e))}")
        else:
            logger.error(f"{message} - detail: {str(e)}")

        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": 500,
                "error": message  # 直接使っても良いが、HTML内では query_params.get 参照形式
            },
            status_code=500
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"redirect_error() - 予期せぬエラー: {str(e)}")

