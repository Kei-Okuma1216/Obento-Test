from fastapi import FastAPI

app = FastAPI()
"""
@app.get("/")
def read_root():
    return {"message": "Hello World"}
"""
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

