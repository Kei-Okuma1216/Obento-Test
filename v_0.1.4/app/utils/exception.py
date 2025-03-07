
from venv import logger
from fastapi import HTTPException
from starlette import status

'''
encoded_message = urllib.parse.quote(f"login_get() Error:  {e.detail}")
'''
# カスタム例外クラス
# 例: raise CustomException(status_code=400, method_name="login_get()", message=str(e))
class CustomException(HTTPException):
    def __init__(self, status_code: int, method_name: str,message: str):
        print(f"🚨 CustomException 発生！ status_code={status_code}, message={message}")
        logger.error(f"例外が発生！- {status_code} - {method_name}, {message}")
        super().__init__(status_code=status_code, detail={
            "method_name": method_name,
            "message": message
            })

# Token期限切れ例外クラス
# 例: raise TokenExpiredException(method_name="verify_token()")
class TokenExpiredException(CustomException):
    def __init__(self, method_name: str, message: str = "トークンの有効期限が切れています。再登録をしてください。"):
        message = "Token has expired"
        print(f"⚠️ TokenExpiredException 発生！ method_name={method_name}, message={message}")  
        
        logger.warning(f"Token期限切れ！- {status.HTTP_401_UNAUTHORIZED} - {method_name}, {message}")
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, method_name=method_name, message=message)

# 認証不許可例外クラス
# 例: raise NotAuthorizedException(method_name="access_protected_resource()")
class NotAuthorizedException(CustomException):
    def __init__(self, method_name: str):

        message = "Not Authorized"
        print(f"⛔ NotAuthorizedException 発生！ method_name={method_name}, message={message}")  
        logger.warning(f"認証不許可！- {status.HTTP_403_FORBIDDEN} - {method_name}, {message}")

        super().__init__(status_code=status.HTTP_403_FORBIDDEN, method_name=method_name, message=message)

# Cookie取得失敗クラス
# 例: raise CookieException(method_name="get_cookie()", detail="有効なセッションがありません")
class CookieException(CustomException):
    def __init__(self, method_name: str, detail: str = "Cookie情報が取得できませんでした"):

        print(f"🚨 CookieException 発生！ method_name={method_name}, message={detail}")  
        logger.error(f"Cookie例外が発生!- {status.HTTP_500_INTERNAL_SERVER_ERROR} - {method_name}, {detail}")
        
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, method_name=method_name, message=detail)

# SQLエラー例外クラス
# 例: raise SQLException(sql_statement=query, method_name="execute_query()", detail=str(e))
class SQLException(CustomException):
    def __init__(self, sql_statement: str, method_name: str, detail: str = "An error occurred with the SQL operation"):

        print(f"🚨 SQLException 発生！ SQL文: {sql_statement}")  # SQL文をログに出力
        full_message = f"{detail}: SQL statement = {sql_statement}"
        logger.critical(f"SQL例外が発生!- {status.HTTP_500_INTERNAL_SERVER_ERROR} - {method_name}, {full_message}")
        
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, method_name=method_name, message=full_message)

# データベース接続エラー例外クラス
# 例: raise DatabaseConnectionException(method_name="connect_to_db()", detail=str(e))
class DatabaseConnectionException(CustomException):
    def __init__(self, method_name: str, detail: str = "Failed to connect to the database"):
        print(f"🔥 DatabaseConnectionException 発生！ method_name={method_name}, message={detail}")
        logger.critical(f"データベース接続エラー！- {status.HTTP_500_INTERNAL_SERVER_ERROR} - {method_name}, {detail}")
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, method_name=method_name, message=detail)

'''
カスタム例外 (CustomException) の raise および catch をテストするには、以下の2つの点をチェックすればOKです。

1. レスポンスのステータスコードが exc.status_code になっているか
2. レスポンスの内容が error.html のテンプレートで正しくレンダリングされているか

'''