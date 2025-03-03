
from fastapi import HTTPException
from starlette import status
'''
encoded_message = urllib.parse.quote(f"login_get() Error:  {e.detail}")
'''     
class CustomException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        print(f"🚨 CustomException 発生！ status_code={status_code}, message={detail}")  # 追加
        super().__init__(status_code=status_code, detail=detail)


# Token期限切れ例外クラス
class TokenExpiredException(CustomException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

# 認証不許可クラス
class NotAuthorizedException(CustomException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized")

# Cookie取得失敗クラス
class CookieException(CustomException):
    def __init__(self, detail: str = "Cookieが取得できませんでした"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

# SQLエラー例外クラス
# 例 raise SQLException(sql_statement=query, detail=str(e))
class SQLException(CustomException):
    def __init__(self, sql_statement: str, detail: str = "An error occurred with the SQL operation"):
        print(f"🚨 SQLException 発生！ SQL文: {sql_statement}")  # SQL文をログに出力
        full_detail = f"{detail}: SQL statement = {sql_statement}"
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=full_detail)

# データベース接続エラー例外クラス
# 例 raise DatabaseConnectionException(detail=str(e))
class DatabaseConnectionException(CustomException):
    def __init__(self, detail: str = "Failed to connect to the database"):
        print("データベース接続の確立に失敗しました。")
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

'''
カスタム例外 (CustomException) の raise および catch をテストするには、以下の2つの点をチェックすればOKです。

1. レスポンスのステータスコードが exc.status_code になっているか
2. レスポンスの内容が error.html のテンプレートで正しくレンダリングされているか

'''