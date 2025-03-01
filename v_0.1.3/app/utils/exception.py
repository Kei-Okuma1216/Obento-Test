
from fastapi import HTTPException
from starlette import status

class CustomException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        print(f"🚨 CustomException 発生！ status_code={status_code}, message={detail}")  # 追加
        super().__init__(status_code=status_code, detail=detail)


# Token期限切れ例外クラス
class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

# 認証不許可クラス
class NotAuthorizedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized")

# Cookie取得失敗クラス
class CookieException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Cookieが取得できませんでした")

