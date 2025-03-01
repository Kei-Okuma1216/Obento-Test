
from fastapi import HTTPException

class CustomException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        print(f"🚨 CustomException 発生！ status_code={status_code}, message={detail}")  # 追加
        super().__init__(status_code=status_code, detail=detail)
