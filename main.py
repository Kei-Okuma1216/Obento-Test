from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import random
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

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
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()

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

@app.post("/register", response_class=HTMLResponse)
async def register(username: str = Form(...), password: str = Form(...)):
    # IDとパスワードに基づいて乱数を生成
    random_number = random.randint(1, 100)
    
    # 乱数に対するシグネチャーの生成
    message = str(random_number).encode()
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # シグネチャーを16進数で表示
    signature_hex = signature.hex()
    
    return f"""
    <html>
        <head>
            <title>登録完了</title>
        </head>
        <body>
            <h1>OKです</h1>
            <p>ユーザー登録が完了しました。</p>
            <p>生成された乱数: {random_number}</p>
            <p>生成されたシグネチャー: {signature_hex}</p>
        </body>
    </html>
    """

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
