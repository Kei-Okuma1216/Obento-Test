from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import random

app = FastAPI()

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
    return f"""
    <html>
        <head>
            <title>登録完了</title>
        </head>
        <body>
            <h1>OKです</h1>
            <p>ユーザー登録が完了しました。</p>
            <p>生成された乱数: {random_number}</p>
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
