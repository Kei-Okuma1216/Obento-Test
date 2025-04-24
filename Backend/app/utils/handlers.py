from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

from .exception import CustomException, NotAuthorizedException   # 必要に応じて修正
from log_unified import logger

templates = Jinja2Templates(directory="templates")

# 共通テンプレート描画関数
def render_error_template(request: Request, template_name: str, status_code: int, message: str, error: str = None):
    context = {"request": request, "message": message, "status_code": status_code}
    if error:
        context["error"] = error
    return templates.TemplateResponse(template_name, context, status_code=status_code)


# グローバル例外ハンドラー登録関数
def register_exception_handlers(app):
    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        logger.error(f"例外ハンドラーが呼ばれました: {exc.detail=}")
        return render_error_template(
            request, "error.html", exc.status_code, exc.detail["message"]
        )

# @app.exception_handler(NotAuthorizedException)
async def not_authorized_exception_handler(request: Request, exc: NotAuthorizedException):
    logger.error(f"NotAuthorizedException: {exc.detail['message']}")
    return render_error_template(
        request, "Unauthorized.html", exc.status_code,
        exc.detail["message"], error="この操作を実行する権限がありません。"
    )


# ✅ ルーターの定義（テスト用API）
test_exception_router = APIRouter()

@test_exception_router.get("/test_exception", tags=["admin"])
async def test_exception():
    logger.error("test_exception() testエラーが発生しました!")
    raise CustomException(400, "これはテストエラーです")

# かつてmain.pyにあった

# デバッグ用 例外ハンドラーの設定

# 実装例
# raise CustomException(400, "token の有効期限が切れています。再登録をしてください。")

# @app.exception_handler(CustomException)
# async def custom_exception_handler(
#     request: Request, exc: CustomException):
#     logger.error(f"例外ハンドラーが呼ばれました: {exc.detail=}")

#     """カスタム例外をキャッチして、HTML にエラーを表示"""
#     return templates.TemplateResponse(
#         "error.html",  # templates/error.html を表示
#         {
#             "request": request,
#             "message": exc.detail["message"],
#             "status_code": exc.status_code
#         },
#         status_code=exc.status_code
#     )

# # グローバルエラーハンドラー
# @app.exception_handler(NotAuthorizedException)
# async def sql_exception_handler(request: Request, exc: NotAuthorizedException):
#     sql = exc.detail.get("sql", "SQL文は提供されていません")
#     logger.error(f"NotAuthorizedException: {exc.detail['message']} | SQL: {sql}")

#     return templates.TemplateResponse(
#         "error.html",
#         {
#             "request": request,
#             "error": "データベース処理で異常が発生しました。",
#             "message": exc.detail["message"],
#             "status_code": exc.status_code
#         },
#         status_code=exc.status_code
#     )

# @app.exception_handler(NotAuthorizedException)
# async def not_authorized_exception_handler(
#     request: Request, exc: NotAuthorizedException):
#     logger.error(f"NotAuthorizedException: {exc.detail['message']}")

#     return templates.TemplateResponse(
#         "Unauthorized.html",  # エラーテンプレート
#         {
#             "request": request,
#             "error": "この操作を実行する権限がありません。",
#             "message": exc.detail["message"],
#             "status_code": exc.status_code,
#         },
#         status_code=exc.status_code
#     )

# # デバッグ用 例外テスト
# @app.get("/test_exception", tags=["admin"])
# async def test_exception():
#     logger.error("test_exception() testエラーが発生しました!")
#     raise CustomException(
#         status.HTTP_400_BAD_REQUEST,
#         "test_exception()",
#         "これはテストエラーです")