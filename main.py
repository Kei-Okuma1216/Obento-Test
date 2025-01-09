from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from datetime import date,datetime, timedelta, timezone
import jwt
from typing import Union # 型ヒント用モジュール
from fastapi.templating import Jinja2Templates # HTMLテンプレート
from starlette.requests import Request

from module1 import create_jwt, verify_jwt, function1, SECRET_KEY

# 自作モジュール my_module.py をimportする
#import my_module

app = FastAPI()
templates = Jinja2Templates(directory="templates")




# 秘密鍵をファイルから読み込む関数:
def load_private_key(key_file: str): 
    with open(key_file, "rb") as key_file:
        private_key = load_pem_private_key(key_file.read(), password=None) 
        return private_key 

#private_key = load_private_key("./my-local.key")
private_key_path = "./my-local.key"
private_key = load_private_key(private_key_path)

# 備考：crtファイルはuvicorn起動だけで使っているため。
#certificate = load_certificate("./my-local.crt")

# 秘密鍵を元に署名を生成する関数:
def sign_message(private_key, message: str, date: date):
    
    # メッセージに日付を追加 
    combined_message = message + str(date)
    
    # 署名を生成
    signature = private_key.sign(
        combined_message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature


"""
venv簡易実行マニュアル
0. OpenSSLで秘密鍵→CSR→自己署名証明書の順につくる
1. main.pyのあるディレクトリでcmdを押してエンターを押す
2. activateする
.\env\Scripts\activate
3. uvicornを使ってHTTPSサーバーを起動する
生成した証明書と秘密鍵を使用して、uvicornでHTTPSサーバーを起動します
uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt
4. ブラウザで、https://localhost:8000 にアクセスする
5. もしエラーになれば、詳細設定ボタン押下後、Localhostにすすむ（安全ではありません）のリンクをクリックする。 
"""

# ユーザー登録ページtest
@app.get("/", response_class=HTMLResponse) 
async def read_root(request: Request): 
    return templates.TemplateResponse("login.html", {"request": request})


# 登録完了画面test
@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        today_date = datetime.today()
        token = create_jwt(username, password, today_date)
        print(f"Generated JWT: {token}")

        # テンプレートにtokenを渡す 
        return templates.TemplateResponse("regist_complete.html", {"request": request, "token": token})
        #return templates.TemplateResponse("regist_complete.html", {"request": request})
    except Exception as e: 
        return f"<html><body><h2>エラー: {str(e)}</h2></body></html>"





# /abcを加えた場合    
@app.get("/abc", response_class=HTMLResponse)
async def read_abc(token: str = Query(...)):
    payload = verify_jwt(token)
    if payload:
        print(f"Token is valid. Payload: {payload}")
        # 日付を取り出す 
        retrieved_date = datetime.fromisoformat(payload["date"]) 
        print(f"Retrieved Date: {retrieved_date}")
        return f""" 
        <html> 
            <head> 
                <title>別のページ</title> 
            </head> 
            <body> 
                <h1>こちらは別のページです</h1> 
                <p>このページは「abc」にアクセスしたときに表示されます。</p>
                <p>Retrieved Date: {retrieved_date}</p>
            </body> 
        </html>
        """
    else:
        print("Invalid or expired token.") 
        return """ 
        <html>
            <head> 
                <title>エラー</title> 
            </head> 
            <body> 
                <h1>トークンが無効または期限切れです</h1> 
                <p>トークンを確認してください。</p> 
            </body> 
        </html> 
        """ 

# ブラウザが要求するfaviconのエラーを防ぐ
# https://github.com/fastapi/fastapi/discussions/11385
favicon_path = 'favicon.ico'  # Adjust path to file

from starlette.responses import FileResponse
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

# 他のモジュールでの誤使用を防ぐ
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
