from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>FastAPI Web Page</title>
        </head>
        <body>
            <h1>Hello, FastAPI!</h1>
            <p>This is a simple web page served with FastAPI.</p>
        </body>
    </html>
    """
# 他のモジュールでの誤使用を防ぐ
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

"""
@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/")
def read_root():
    # ここで単純に localhost にアクセスした場合
    return {"signature": "ここにBase64Encode文字列がズラズラと書いてある。"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.get("/login/{user_id}")
def read_item(user_id: int, password: str = None):
    return {"user_id": user_id, "password": password}
"""
