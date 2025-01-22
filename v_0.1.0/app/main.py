from http.cookiejar import Cookie
from fastapi import Cookie, FastAPI, Form, Header, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from datetime import datetime
from typing import Optional, Union # 型ヒント用モジュール
from fastapi.templating import Jinja2Templates # HTMLテンプレート
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from local_jwt_module import create_jwt, verify_jwt
ALGORITHM = "HS256"
import sys 
print(sys.path)
from init_module import init_database, insert_mock_user, get_connection, select_mock_user

app = FastAPI()
templates = Jinja2Templates(directory="templates")
#init_database()

@app.exception_handler(StarletteHTTPException) 
async def http_exception_handler(request, exc): 
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)

# cd C:\Obento-Test\v_0.1.0\app
# .\env\Scripts\activate
# uvicorn main:app --host 127.0.0.1 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt

# お弁当屋の注文確認
@app.get("/today", response_class=HTMLResponse)
def shop_today_order(request: Request, hx_request: Optional[str] = Header(None)):
    orders = [
        {'number':"1", 'company':"テンシステム", 'name':"大隈　慶1", "menu": 1, "value":1, "date": "2025-1-22"},
        {'number':"2", 'company':"テンシステム", 'name':"大隈　慶2", "menu": 1, "value":1, "date": "2025-1-22"},
        {'number':"3", 'company':"テンシステム", 'name':"大隈　慶3", "menu": 100, "value":1, "date": "2025-1-22"}
    ]
    context = {'request': request, 'orders': orders}
    print(f"Context: {context}")
    if hx_request:
        return templates.TemplateResponse("table.html",context)
    return templates.TemplateResponse(
        "store_orders_today.html",context)

# 最初にアクセスするページ
# https://127.0.0.1:8000
@app.get("/", response_class=HTMLResponse) 
async def read_root(request: Request): 
    token = request.cookies.get("token") 
    if token: 
        # ここでtokenの期限切れ確認する
        payload = verify_jwt(token)
        if payload == None:
            # tokenは有効期限切れ
            return RedirectResponse(url="/token_error")
        else:
            # tokenは有効
            return RedirectResponse(url="/token_yes")
    else:
        return templates.TemplateResponse(
            "login.html", {"request": request})

# tokenがある場合
@app.get("/token_yes", response_class=HTMLResponse) 
async def read_yes(request: Request): 
    return templates.TemplateResponse(
        "regist_complete.html",{"request": request})

# tokenがある場合
@app.get("/regist_complete", response_class=HTMLResponse) 
async def read_yes(request: Request): 
    return templates.TemplateResponse(
        "regist_complete.html",{"request": request})


# tokenがない場合
id_counter = 1
def get_next_id():
    return id_counter + 1

# 登録中画面 login.htmlでOKボタン押下で遷移する
@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request, response: Response,
    userid: str = Form(...), password: str = Form(...)):
    try:
        # ユーザー登録
        #print(userid)
        #print("select_mock_user(userid)実行前")
        result = await select_mock_user(userid, request)
        #print("select_mock_user(userid)実行後")
        #print(result)
        #print("result実行後")
        if  result is None:
            # ユーザーなし
            print("ユーザーなし")
            token = create_jwt(userid, password, datetime.today())
            response.set_cookie(key="token", value=token)
            print(f"- Generated JWT: {token}")

            page = templates.TemplateResponse(
                "regist_complete.html",
                {"request": request, "token": token})
            
            # pageに response.cookiesを追加
            page.headers.raw.extend(response.headers.raw)
            return page
        else:
            print("ユーザーあり")
            # ユーザーあり
            token2 = request.cookies.get("token")
            print(f"- すでに持っている JWT: {token2}")
            # デバッグで持てていない
            #print(result['userid'])
            #print(result['password'] + " : " + password)
            if result['password'] == password:  # パスワードチェック
                return templates.TemplateResponse(
                    "regist_complete.html",
                    {"request": request, "token": token2},
                    status_code=200)
            else:
                print(f"Error: {str(e)}")
                return templates.TemplateResponse(
                    "error.html",
                    {"request": request, "Invalid credentials": str(e)},
                    status_code=400)
        
    except Exception as e: 
        print(f"Error: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)})


# token確認画面 
@app.get("/check", response_class=HTMLResponse)
async def check_token(
    request: Request, token: str = Cookie(None)):
    try:
        if token is None: 
            return templates.TemplateResponse(
                "token_error.html",
                {"request": request,
                 "error": "Token is missing"},
                status_code=400)
                     
        payload = verify_jwt(token)
        if payload:
            print(f"Token is valid. Payload: {payload}")
            
            # 日付を取り出す 
            token_date = datetime.fromisoformat(
                payload["date"]) 
            print(f"Retrieved Date: {token_date}")
            
            # date.html
            return templates.TemplateResponse(
                "date.html",
                {"request": request, "token": token,
                "retrieved_date": token_date, "current_date": datetime.now()})
        else:
            # token_error.html
            print("Invalid or expired token.") 
            return templates.TemplateResponse(
                "token_error.html",
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
