from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
#import random
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
#from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
#from OpenSSL import crypto

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

app = FastAPI()

# RSAキーの生成（実際のアプリケーションでは、キーの管理方法を適切にする必要があります）
"""private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()
"""
# 秘密鍵をファイルから読み込む関数:
def load_private_key(key_file: str): 
    with open(key_file, "rb") as key_file:
        private_key = load_pem_private_key(key_file.read(), password=None) 
        return private_key 
private_key = load_private_key("./my-local.key")

# 署名を生成する関数:
def sign_message(private_key, message: str):
    signature = private_key.sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature
# 備考：crtファイルはuvicorn起動だけで使っているため。
#certificate = load_certificate("./my-local.crt")

# 登録完了画面
@app.post("/register", response_class=HTMLResponse)
async def register(username: str = Form(...),password: str = Form(...)):
    try:
        # IDとパスワードに基づいてメッセージを生成 
        message = username + password 
        
        # 署名を生成 
        signature = sign_message(private_key, message) 
        signature_hex = signature.hex()
        
        return f"""
        <html>
            <head>
                <title>登録完了</title>
            </head>
            <body>
                <h1>OKです</h1>
                <p>ユーザー登録が完了しました。</p>
                <p>生成されたシグネチャー: {signature_hex}</p>
            </body>
        </html>"""
    except Exception as e: 
        return f"<html><body><h2>エラー: {str(e)}</h2></body></html>"

# ユーザー登録ページ
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>ここはユーザー登録ページです</title>
        </head>
        <body>
            <h1>こんにちは！</h1>
            <form action="/register" method="post">
                <label for="username">ID:</label><br>
                <input type="text" id="username" name="username"><br>
                <label for="password">パスワード:</label><br>
                <input type="password" id="password" name="password"><br>
                <input type="submit" value="OK">
            </form>
        </body>
    </html>
    """
# /abcを加えた場合    
@app.get("/abc", response_class=HTMLResponse)
async def read_abc():
    return """
    <html>
        <head>
            <title>別のページ</title>
        </head>
        <body>
            <h1>こちらは別のページです</h1>
            <p>このページは「abc」にアクセスしたときに表示されます。</p>
        </body>
    </html>
    """

# 他のモジュールでの誤使用を防ぐ
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
