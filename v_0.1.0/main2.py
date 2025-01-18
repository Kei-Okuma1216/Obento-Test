from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

import jwt # pip install pyjwt

from my_package import SECRET_KEY, ALGORITHM,create_token
from fastapi.templating import Jinja2Templates # 



app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.exception_handler(StarletteHTTPException) 
async def http_exception_handler(request: Request, exc: StarletteHTTPException): 
    return HTMLResponse( f""" <html> <head> <title>{exc.status_code} Error</title> </head> <body> <h1>{exc.status_code} Error</h1> <p>{exc.detail}</p> </body> </html> """, status_code=exc.status_code )

# トークン生成リクエストのスキーマ
class TokenRequest(BaseModel):
    username: str
    


# ユーザー登録ページ
@app.get("/", response_class=HTMLResponse) 
async def read_root(request: Request): 
    token = request.cookies.get("token") 
    if token:
        return RedirectResponse(url="/cde")
    
    return templates.TemplateResponse("login.html", {"request": request})

@app.exception_handler(StarletteHTTPException) 
async def http_exception_handler(request, exc): 
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)


# POSTメソッドでトークンを生成
@app.post("/generate-token")
def generate_token(request: TokenRequest):
    try:
        token = create_token(request.username)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {e}")

# (ブラウザ用に)GETメソッドでもトークンを生成
# https://127.0.0.1:8000/generate-token?username=testuser
@app.get("/generate-token")
def generate_token_get(username: str):
    try:
        token = create_token(username)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {e}")

# トークン検証リクエストのスキーマ
class TokenVerificationRequest(BaseModel):
    token: str

# curl -X GET "http://127.0.0.1:8000/generate-token?username=testuser"

# curl -X POST "http://127.0.0.1:8000/verify-token" -H "Content-Type: application/json" -d "{\"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcwMDAwMDAwMCwiaWF0IjoxNzAwMDAwMDAwLCJuYmYiOjE3MDAwMDAwMDB9.abc123\"}"

# トークン検証エンドポイント
@app.post("/verify-token")
def verify_token(request: TokenVerificationRequest):
    try:
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        print("payload" + payload.json())
        return {"payload": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
