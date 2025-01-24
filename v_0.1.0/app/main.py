from fastapi import FastAPI, Form, Header, Response, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from http.cookies import SimpleCookie
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from typing import Optional, Union # 型ヒント用モジュール

from local_jwt_module import create_jwt, verify_jwt
from mock_db_module import init_database, select_user, select_today_orders

ALGORITHM = "HS256"

app = FastAPI()
templates = Jinja2Templates(directory="templates")
init_database()


# Token期限切れ例外クラス
class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
# 認証不許可クラス
class NotAuthorizedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized")
    
@app.exception_handler(StarletteHTTPException) 
async def http_exception_handler(request, exc): 
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)

# 起動方法
# cd C:\Obento-Test\v_0.1.0\app
# .\env\Scripts\activate
# uvicorn main:app --host 127.0.0.1 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt

# お弁当屋の注文確認
@app.get("/today", response_class=HTMLResponse, tags=["order"])
def shop_today_order(request: Request,
    hx_request: Optional[str] = Header(None)):
    # 権限チェック
    permission = request.cookies.get("permission")
    if permission != 2:
        raise HTTPException(status_code=403, detail="Not Authorized")
    
    # 昨日の全注文
    orders = select_today_orders(1)
    # ここで取れていない!
    print('orders開始')
    print(type(orders))
    if orders is None:
        print('ordersなし')
    else:
        print(orders)
    
    ''' 
    orders = [
        {'order_id': 1, 'company':"テンシステム", 'name':"大隈　慶1", "menu": 1, "amount":1, "order_date": "2025-01-23 10:32"},
        {'order_id': 2, 'company':"テンシステム", 'name':"大隈　慶2", "menu": 1, "amount":1, "order_date": "2025-01-23 10:33"},
        {'order_id': 3, 'company':"テンシステム", 'name':"大隈　慶3", "menu": 100, "amount":3, "order_date": "2025-01-23 10:34"}
    ]
    ''' 
   
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
    print("/で tokenを取得")
    print(token)
    if token: 
        payload = verify_jwt(token)
        print("/で payloadを取得")
        print(payload)

        if payload == None:
            return RedirectResponse(url="/token_error")
        else:
            # tokenは有効
            print("/で payloadは有効")
            print(payload)    
            return RedirectResponse(url="/regist_complete")
    else:
        return templates.TemplateResponse(
            "login.html", {"request": request})

# tokenを持っている場合
@app.get("/regist_complete", response_class=HTMLResponse) 
async def regist_complete(
    request: Request): 
    # もしCookieのpermission=2ならば、/todayにリダイレクト
    if request.cookies.get("permission") == "2":
        print("permission=2")
        return RedirectResponse(url="/today")
    
    return templates.TemplateResponse(
        "regist_complete.html",{"request": request})


# tokenがない場合
# 登録中画面 login.htmlでOKボタン押下で遷移する
@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request, response: Response,
    userid: str = Form(...), password: str = Form(...)):
    try:
        # ユーザー登録
        _user = await select_user(userid)
        
        if  _user is None:
            print("ユーザーなし")
            token = create_jwt(userid, password, datetime.today())
            response.set_cookie(key="token", value=token)
            print(f"- Generated JWT: {token}")

            response.set_cookie(key="permission", value="2")

            page = templates.TemplateResponse(
                "regist_complete.html",
                {"request": request, "token": token})
            
            # pageに response.cookiesを追加
            page.headers.raw.extend(response.headers.raw)
            
            return page
        else:
            print("ユーザーあり")
            token2 = request.cookies.get("token")
            print(f"- すでに持っている JWT: {token2}")
            # しかしデバッグでは持てていない
            # ここで権限を判定できないか？
            permission = request.cookies.get("permission")
            print(f"- 権限: {permission}")

            # パスワードチェック
            if _user['password'] == password:  
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
    request: Request, token: str = SimpleCookie(None)):
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
