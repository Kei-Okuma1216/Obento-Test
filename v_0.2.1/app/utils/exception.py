# database/exception.py
from venv import logger
from fastapi import HTTPException
from starlette import status

# encoded_message = urllib.parse.quote(f"login_get() Error:  {e.detail}")

# カスタム例外クラス
class CustomException(HTTPException):
    ''' 例: raise CustomException(
                status_code=400,
                method_name="login_get()",
                message=str(e))
    '''
    def __init__(self,
                 status_code: int = 500,
                 method_name: str = "",
                 message: str = ""):
        #print(f"🚨 CustomException 発生！ status_code={status_code}, message={message}")
        logger.error(f"CustomException が発生！- {status_code} - {method_name}, {message}")
        super().__init__(
            status_code=status_code,
            detail={
            "method_name": method_name,
            "message": message
            })

# Token期限切れ例外クラス
class TokenExpiredException(CustomException):
    ''' 例： raise TokenExpiredException(
                 method_name="verify_token()")
        備考：root()でtokenの初回取得は、この例外を使用しない。
        理由：画面が停止するため
    '''
    def __init__(
        self,
        method_name: str,
        detail: str = f"トークンの有効期限が切れています。再登録してください。",
        exception: Exception = None  # 例外オブジェクトを追加
    ):
        message = detail  # `message` に `detail` を渡す

        # `exception` がある場合は、詳細なメッセージを付加
        if exception:
            message += f" (原因: {str(exception)})"

        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, method_name=method_name,
            message=detail)  # `message` に変換した `detail` を渡す

# 認証不許可例外クラス
class NotAuthorizedException(CustomException):
    ''' 例: raise NotAuthorizedException(
                method_name="access_protected_resource()")'''
    def __init__(
        self,
        method_name: str,
        detail: str = f"認証不許可",
        exception: Exception = None  # 例外オブジェクトを追加
    ):
        message = detail  # `message` に `detail` を渡す

        # `exception` がある場合は、詳細なメッセージを付加
        if exception:
            message += f" (原因: {str(exception)})"

        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, method_name=method_name,
            message=detail)

# Cookie取得失敗クラス
class CookieException(CustomException):
    ''' 例:
        except Exception as e:
            raise CookieException(
                method_name="get_max_age()",
                detail="max-age取得でエラーが発生しました。",
                exception=e
            )
    '''
    def __init__(
        self,
        method_name: str,
        detail: str = f"Cookie情報が取得できませんでした。",
        exception: Exception = None  # 例外オブジェクトを追加
    ):
        message = detail  # `message` に `detail` を渡す

        # `exception` がある場合は、詳細なメッセージを付加
        if exception:
            message += f" (原因: {str(exception)})"

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, method_name=method_name,
            message=detail)  # `message` に変換した `detail` を渡す

# SQLエラー例外クラス
class SQLException(CustomException):
    '''
        備考：SQLException は Python に標準で用意されていない例外です。
        SQLite を使っているなら、sqlite3.DatabaseError または sqlite3.OperationalError などの例外が発生する可能性が高いです。
        PostgreSQL や MySQL なら asyncpg.exceptions.PostgresError や aiomysql.Error などをキャッチすべきです。
        例: 
        except sqlite3.DatabaseError as e:
            raise SQLException(
                sql_statement=query,
                method_name="execute_query()",
                detail="SQL実行中にエラーが発生しました",
                exception=e  # `e` を渡す
            )
    '''
    def __init__(
        self,
        sql_statement: str,
        method_name: str,
        detail: str = "An error occurred with the SQL operation",
        exception: Exception = None  # 例外オブジェクトを追加
    ):
        # 例外がある場合、メッセージに追加
        message = f"{detail}: SQL statement = {sql_statement}"
        if exception:
            message += f" (原因: {str(exception)})"

        # `logger.critical` の削除 → `CustomException` に処理を任せる
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            method_name=method_name,
            message=message
        )

# データベース接続エラー例外クラス
class DatabaseConnectionException(CustomException):
    ''' 例:
    except Exception as e:
        raise DatabaseConnectionException(
            method_name="connect_to_db()",
            detail="データベース接続に失敗しました。",
            exception=e  # `e` を渡す
        )
    '''
    def __init__(
        self,
        method_name: str,
        detail: str = "Failed to connect to the database",
        exception: Exception = None  # 例外オブジェクトを追加
    ):
        # 例外がある場合、メッセージに追加
        message = detail
        if exception:
            message += f" (原因: {str(exception)})"

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            method_name=method_name,
            message=message
        )


'''
カスタム例外 (CustomException) の raise および catch をテストするには、以下の2つの点をチェックすればOKです。

1. レスポンスのステータスコードが exc.status_code になっているか
2. レスポンスの内容が error.html のテンプレートで正しくレンダリングされているか

'''