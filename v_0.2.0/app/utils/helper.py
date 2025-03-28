# helper.py
# 必ずmain.pyとセットにすること
from typing import Optional
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from database.sqlite_database import insert_new_user, select_user
from local_jwt_module import get_new_token
from utils.utils import log_decorator, set_all_cookies
from utils.exception import CustomException, NotAuthorizedException, SQLException
from log_config import logger
from schemas.schemas import UserBase, UserResponse
import bcrypt

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

@log_decorator
async def get_main_url(permission: int) -> str:
    try:
        # リダイレクト先の選択 1: "/order_complete",
        redirect_url = {
            1: "/users/order_complete",
            2: "/manager/me",
            10: "/shops/me",
            99: "/admin/me"}.get(permission, "/error")
        logger.debug(f"redirect_url: {redirect_url}")

        return redirect_url
    except Exception as e:
        raise CustomException(status_code=400,
                method_name="get_main_url()", message=str(e))

@log_decorator
async def create_auth_response(
    username: str, permission: int, redirect_url: str) -> Response:
    try:
        """
        ユーザー情報を元に新しいトークンを生成し、Cookie を設定したリダイレクトレスポンスを返す。
        """
        data = {"sub": username, "permission": permission}
        access_token, expires = get_new_token(data)
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
        raise CustomException(method_name="create_auth_response()")

@log_decorator
def redirect_login(request: Request, message: str=None, error: str=None, e: Exception=None):
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
        raise CustomException(
            status.HTTP_404_NOT_FOUND,
            "redirect_login()",
            f"Error: {e.detail}")

@log_decorator # eも組み込みたい
def redirect_error(request: Request, message: str, e: Exception):
    '''error.htmlに戻る'''
    try:
        logger.error(f"{message} - detail:{e.detail["message"]}")
        #logger.error(e.detail["message"])
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": message})
    except HTTPException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_404_NOT_FOUND,
            "redirect_error()",
            f"Error: {e.detail}")

@log_decorator
def hash_password(password: str) -> str:
    """パスワードをハッシュ化する"""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)

    return hashed_password.decode()  # バイト列を文字列に変換

@log_decorator
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """入力されたパスワードがハッシュと一致するか検証
       True: 一致, False: 不一致"""
    try:
        if(bcrypt.checkpw(plain_password.encode(), hashed_password.encode())):
            return True
        else:
            return False
        #return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception as e:
        raise CustomException("verify_password()", message=str(e))

@log_decorator
async def authenticate_user(username, password, name) -> Optional[UserBase]:
    """ ログイン認証 """
    try:
        user : UserResponse = await select_user(username) # UserCreateにするべき

        if user is None:
            logger.debug(f"ユーザーが存在しません: {username}")
            await insert_new_user(username, password, name)
            user: UserResponse = await select_user(username) # UserResponseにするべき

        logger.info(f"authenticate_user() - 認証試行: {user.username}")

        # ハッシュ化されたパスワードと入力パスワードを比較
        if not verify_password(password, user.get_password()):
            ''' 注意：1回目は admin.pyにある、/me/update_existing_passwordsを実行して、Userテーブルのパスワードをハッシュ化する必要がある '''
            #logger.info("パスワードが一致しません")
            #return None
            raise NotAuthorizedException(
                method_name="verify_password()",
                detail="パスワードが一致しません"
            )

        data = {
            "sub": user.get_username(),
            "permission": user.get_permission()
        }
        access_token, expires = get_new_token(data)
        user.set_token(access_token)        
        user.set_exp(expires)

        logger.info(f"認証成功: {user.username}")

        return user

    except (NotAuthorizedException, SQLException) as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            f"authenticate_user()",
            f"予期せぬエラー{e}")
