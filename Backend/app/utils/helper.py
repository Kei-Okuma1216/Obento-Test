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
    7. redirect_unauthorized(request: Request, message: str, code: int = 403):
    8. redirect_register(request: Request, username: str, error_message: str):
'''
from fastapi import HTTPException, Request, Response, status

from schemas.user_schemas import UserResponse
from utils.decorator import log_decorator
from utils.cookie_helper import set_all_cookies

from log_unified import logger

from config.config_loader import load_permission_map, load_holiday_map
permission_map = load_permission_map()
holiday_map = load_holiday_map()

@log_decorator
async def get_main_url(permission: str, **kwargs) -> str:
    permission_map = load_permission_map()
    url_template = permission_map.get(str(permission))
    
    if not url_template:
        raise ValueError("権限に対応するURLが見つかりません")

    try:
        # テンプレート展開
        return url_template.format(**kwargs)
    except KeyError as e:
        # 未設定項目があれば空文字列に置換
        return url_template.format_map(DefaultDict("", kwargs))

# 補助クラス: 空文字返却用
class DefaultDict(dict):
    def __missing__(self, key):
        return ""

from models.user import select_user_by_id
from fastapi.responses import JSONResponse

@log_decorator
async def get_account_by_id_or_404_response(user_id: int):

    user_info = await select_user_by_id(user_id)  # user_id で検索
    if user_info is None:
        raise HTTPException(status_code=404, detail=f"ユーザーID {user_id} が見つかりません")

    print(f"{user_info=}")
    response_data = UserResponse(
        user_id=user_info.user_id,
        username=user_info.username,
        name=user_info.name,
        company_id=user_info.company_id,
        shop_name=user_info.shop_name,
        menu_id=user_info.menu_id,
        permission=user_info.permission
    )
    return JSONResponse(content=response_data.model_dump())


from fastapi import HTTPException, status, Response
from fastapi.responses import RedirectResponse
from core.security import get_access_token
from utils.cookie_helper import set_all_cookies

@log_decorator
# ユースケース層に近い関数なので、ログ出力は必要
async def create_auth_response(
    username: str,
    permission: int,
    redirect_url: str
) -> Response:
    try:
        # 入力バリデーション
        if not isinstance(username, str) or not username.strip():
            logger.warning("create_auth_response() - usernameが無効")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なユーザー名です"
            )

        if not isinstance(permission, int):
            logger.warning("create_auth_response() - permissionが無効")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なパーミッション値です"
            )

        if not isinstance(redirect_url, str) or not redirect_url.startswith("/"):
            logger.warning("create_auth_response() - redirect_urlが無効")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なリダイレクトURLです"
            )

        # トークン生成
        data = {"sub": username, "permission": permission}
        access_token, expires = get_access_token(data)

        new_data = {
            "sub": username,
            "permission": permission,
            "token": access_token,
            "expires": expires
        }

        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

        try:
            set_all_cookies(response, new_data)
        except Exception as cookie_error:
            logger.exception("Cookie設定中にエラーが発生しました")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cookie設定に失敗しました"
            )

        # return response

    except (KeyError, TypeError, ValueError) as e:
        logger.exception("create_auth_response() - 入力データ形式エラー")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="トークン生成に必要なデータが不正です"
        )
    except HTTPException:
        raise  # 明示的に投げたHTTPExceptionはそのまま返す
    except Exception as e:
        logger.exception("create_auth_response() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認証レスポンス生成中にサーバーエラーが発生しました"
        )
    else:
        logger.info(f"Auth success: user={username}, permission={permission}, redirect={redirect_url}")
        return response


from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound
templates = Jinja2Templates(directory="templates")

@log_decorator
def redirect_login(
    request: Request,
    message: str = None,
    error: str = None,
    e: Exception = None
):
    """login.html にリダイレクトする（例外対応付き）"""
    try:
        if error:
            logger.error(f"Redirect Login - {error}")
        if message:
            logger.info(f"Redirect Login - {message}")

    except TemplateNotFound:
        logger.exception("login.html テンプレートが見つかりません")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="テンプレートが見つかりません"
        )
    except (AttributeError, TypeError) as ex:
        logger.exception("リクエストまたはデータの形式に問題があります")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ログイン画面描画のリクエストデータが不正です"
        )
    except Exception as ex:
        logger.exception("redirect_login() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログイン画面の描画中にエラーが発生しました"
        )
    else:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "message": message,
                "error": error
            }
        )


# ログイン成功時のリダイレクト
# 正常系
@log_decorator
def redirect_login_success(request: Request, message: str = "ようこそ"):
    """ログイン成功時に login.html へリダイレクト（例外対応付き）"""
    try:
        logger.info(f"Redirect Login Success - {message}")

    except TemplateNotFound:
        logger.exception("login.html テンプレートが見つかりません")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログインページが利用できません"
        )
    except (AttributeError, TypeError) as ex:
        logger.exception("リクエストまたはメッセージの形式が不正です")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="リダイレクト中のリクエストデータが不正です"
        )
    except Exception as ex:
        logger.exception("redirect_login_success() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログイン成功リダイレクト中にエラーが発生しました"
        )
    else:
        return templates.TemplateResponse(
            "login.html", {"request": request, "message": message, "error": None}
        )


# エラー時のリダイレクト
# 異常系
@log_decorator
def redirect_login_failure(request: Request, error: str, e: Exception = None):
    """ログイン失敗時に login.html へリダイレクト（例外対応付き）"""
    try:
        logger.info(f"Redirect Login Failure - {error}")
        if e:
            detail_message = getattr(e, "detail", str(e))
            logger.error(f"Error detail: {detail_message}")

    except TemplateNotFound:
        logger.exception("login.html テンプレートが見つかりません")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログインページが利用できません"
        )
    except (AttributeError, TypeError) as ex:
        logger.exception("リクエストまたはエラーメッセージの形式が不正です")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="リダイレクト中のリクエストデータが不正です"
        )
    except Exception as ex:
        logger.exception("redirect_login_failure() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログイン失敗リダイレクト中にエラーが発生しました"
        )
    else:
        return templates.TemplateResponse(
            "login.html", {"request": request, "message": None, "error": error}
        )


@log_decorator
async def redirect_error(request: Request, message: str, e: Exception = None):
    """error.html にリダイレクトし、クエリにエラー内容を表示"""
    try:
        status_code = 500
        detail_message = None

        if e:
            if isinstance(e, HTTPException):
                status_code = e.status_code
                detail_message = e.detail
            else:
                detail_message = getattr(e, "detail", str(e))
        else:
            detail_message = "詳細情報はありません"

    except TemplateNotFound:
        logger.exception("error.html テンプレートが見つかりません")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="エラーページが利用できません"
        )
    except (AttributeError, TypeError) as ex:
        logger.exception("リクエストまたはデータの形式に問題があります")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="エラーページ表示中にリクエストデータが不正です"
        )
    except HTTPException:
        # 既にHTTPExceptionならそのまま再スロー
        raise
    except Exception as ex:
        logger.exception("redirect_error() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="エラーページ表示中にサーバーエラーが発生しました"
        )
    else:
        logger.error(f"{message} - detail: {detail_message}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": status_code,
                "error": message
            },
            status_code=status_code
        )

@log_decorator
def redirect_unauthorized(request: Request, message: str, code: int = 403):
    """Unauthorized.html にリダイレクト（例外対応付き）"""
    try:
        logger.error(f"Unauthorized - {message}")

    # else:
        print("redirect_unauthorized() が呼び出されました")  # ← 追加
        return templates.TemplateResponse(
            "Unauthorized.html",
            {
                "request": request,
                "status_code": code,
                "message": message
            },
            status_code=code
        )

    except TemplateNotFound:
        logger.exception("Unauthorized.html テンプレートが見つかりません")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認可エラーページが利用できません"
        )

    except (AttributeError, TypeError) as ex:
        logger.exception("リクエストまたはメッセージデータの形式に問題があります")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="認可エラーページ表示中にリクエストデータが不正です"
        )

    except Exception as ex:
        logger.exception("redirect_unauthorized() - 予期せぬエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認可エラーページ表示中にサーバーエラーが発生しました"
        )

def redirect_register(request: Request, username: str, error_message: str):
    """
    ユーザー登録画面へのリダイレクトレスポンスを返すヘルパー関数。
    """
    logger.warning(f"/register - 既存ユーザー名: {username}")
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": error_message},
        status_code=400
    )

