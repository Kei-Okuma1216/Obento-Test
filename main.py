from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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
            <p>あなたはまだユーザー登録が済んでいません。</p>
            <p>このページでユーザー登録をしましょう！！</p>
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

