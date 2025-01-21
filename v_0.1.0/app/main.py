from http.cookiejar import Cookie
from fastapi import Cookie, FastAPI, Form, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from datetime import datetime
from typing import Union # 型ヒント用モジュール
from fastapi.templating import Jinja2Templates # HTMLテンプレート
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from local_jwt_module import create_jwt, verify_jwt, ALGORITHM, SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



app = FastAPI()
templates = Jinja2Templates(directory="templates")
# 
# uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt


# 最初にアクセスするページ
@app.get("/", response_class=HTMLResponse) 
async def read_root(request: Request): 
    # もしtokenがついていたら、独自のページに遷移する。
    token = request.cookies.get("token") 
    if token: 
        return RedirectResponse(url="/token_yes")
    else:
        return templates.TemplateResponse("login.html", {"request": request})

@app.exception_handler(StarletteHTTPException) 
async def http_exception_handler(request, exc): 
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)

id_counter = 1
def get_next_id():
    return id_counter + 1

# 登録中画面
@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    '''
    https://127.0.0.1:8000でアクセスする
    '''
    try:
 
        token = create_jwt(username, password, datetime.today())
        response.set_cookie(
            key="token",
            value=token
        )
        print(f"- Generated JWT: {token}")

        page = templates.TemplateResponse(
            "regist_complete.html", {"request": request, "token": token})
        
        # pageに response.cookiesを追加
        page.headers.raw.extend(response.headers.raw)
        return page
    
    except Exception as e: 
        print(f"Error: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)})

# tokenがある場合
@app.get("/token_yes", response_class=HTMLResponse) 
async def read_yes(request: Request): 
    return templates.TemplateResponse(
        "token_yes.html",{"request": request})

# token確認画面 
@app.get("/check", response_class=HTMLResponse)
async def check_token(
    request: Request, token: str = Cookie(None)):
    try:
        if token is None: 
            return templates.TemplateResponse(
                "token_error.html", {"request": request, "error": "Token is missing"}, status_code=400)
                     
        payload = verify_jwt(token)
        if payload:
            print(f"Token is valid. Payload: {payload}")
            
            # 日付を取り出す 
            token_date = datetime.fromisoformat(payload["date"]) 
            print(f"Retrieved Date: {token_date}")
            
            # date.html
            return templates.TemplateResponse("date.html",
                {"request": request, "token": token,
                "retrieved_date": token_date, "current_date": datetime.now()})
        else:
            # token_error.html
            print("Invalid or expired token.") 
            return templates.TemplateResponse("token_error.html",
                {"request": request, "token": token},status_code=400)
    except Exception as e:
        print(f"Error: {str(e)}") 
        return templates.TemplateResponse( 
            "error.html", {"request": request, "error": str(e)})

    
    
# ブラウザが要求するfaviconのエラーを防ぐ
# https://github.com/fastapi/fastapi/discussions/11385
favicon_path = './static/favicon.ico'  # Adjust path to file

# Ensure favicon.ico is accessible
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
     return FileResponse(favicon_path)
 
# Mount the directory where favicon.ico is located 
# faviconのマウント
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# 他のモジュールでの誤使用を防ぐ
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, timeout_keep_alive=100)
