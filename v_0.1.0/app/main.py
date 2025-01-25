from functools import wraps
import logging
from fastapi import FastAPI, Form, Header, Response, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from http.cookies import SimpleCookie
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from typing import Optional, Union # 型ヒント用モジュール

from local_jwt_module import TokenExpiredException, create_jwt, verify_jwt
from mock_db_module import init_database, select_user, select_today_orders, update_user, delete_database

ALGORITHM = "HS256"

app = FastAPI()
templates = Jinja2Templates(directory="templates")

#init_database()
#delete_database()
@app.exception_handler(StarletteHTTPException) 
async def http_exception_handler(request, exc): 
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)

# ログ用の設定
logging.basicConfig(level=logging.INFO)

# カスタムデコレーターを定義
def log_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logging.info("- %s 前", func.__name__)
        result = await func(*args, **kwargs)
        logging.info("- %s 後", func.__name__)
        return result
    return wrapper

# 最初にアクセスするページ
# https://127.0.0.1:8000
#@app.get("/", response_class=HTMLResponse, tags=["user"]) 
#@log_decorator  # デコレーターを適用
#async def read_root(): 
#    return RedirectResponse(url="/check")

# トークンチェック 
@app.get("/", response_class=HTMLResponse, tags=["user"])
@log_decorator
async def check_token(request: Request, response: Response):
    try:
        token = request.cookies.get("token") 
        print(token)
        # tokenがない場合
        if token is None: 
            print("tokenはありません")
            return RedirectResponse(url="/login")

        # tokenが存在する場合の処理
        return templates.TemplateResponse("protected_page.html", {"request": request})
    
        # tokenがある場合
        payload = verify_jwt(token)
        print(payload)
        if payload is None:
            print(f"Token is valid. Payload: {payload}")
            return templates.TemplateResponse("token_error.html", {"request": request, "error": "Token is missing"},status_code=400)
        
        # 生成日
        create_date = datetime.fromisoformat(payload["create-date"]) 
        if create_date is None:
            print("Token create_date is corrupsed.")
            raise TokenExpiredException()
        print(f"Retrieved Date: {create_date}")
        
        # 有効期限
        expire_date = payload["exp"]
        if expire_date is None:
            print("Token expire_date is corrupsed.")
            raise TokenExpiredException()                
        if expire_date < datetime.now():
            print("Token has expired.")
            raise TokenExpiredException()
        print(f"Expire Date: {expire_date}")

        print("token is OK")       
        # ここで権限が渡されていない    
        #return RedirectResponse(url="/register")
        response = RedirectResponse(url="/check")
        response.set_cookie(key="token", value=token)
        return response
    
    except Exception as e:
        print(f"Error: {str(e)}") 
        return templates.TemplateResponse( 
            "error.html", {"request": request, "error": str(e)})

# -----------------------------------------------------
# ログイン画面を表示するエンドポイント
@app.get("/login", response_class=HTMLResponse, tags=["user"])
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ログイン処理用エンドポイント
@app.post("/login", response_class=HTMLResponse, tags=["user"])
async def login(request: Request, userid: str = Form(...), password: str = Form(...)):
    # ここに認証処理を追加
    if userid == "valid_user" and password == "valid_password":  # サンプルの認証ロジック
        response = RedirectResponse(url="/check", status_code=303)
        response.set_cookie(key="token", value="valid_token")  # サンプルトークン設定
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
# -----------------------------------------------------

# tokenがない場合
# 登録中画面 login.htmlでOKボタン押下で遷移する
@app.post("/register", response_class=HTMLResponse, tags=["user"])
async def register(
    request: Request, response: Response,
    userid: str = Form(...), password: str = Form(...)):
    try:
        # ユーザー登録
        print("ユーザー登録")
        print(userid)
        _user = select_user(userid)
        if _user is None:
            print("User not found or error occurred")

        print(_user)  # キーワード引数として展開
        if  _user is None:
            print("ユーザー登録なし")
            token = create_jwt(userid, password)

            # tokenをUPDATEする
            print("update token前")
            update_user(_user['user_id'], token)
            print("update token後")
            
            response.set_cookie(key="token", value=token)
            print(f"- Generated JWT: {token}")

            print(f'permission: {_user["permission"]}')
            response.set_cookie(key="permission", value=_user['permission'])

            page = templates.TemplateResponse(
                "regist_complete.html",
                {"request": request, "token": token})
            
            # pageに response.cookiesを追加
            page.headers.raw.extend(response.headers.raw)
            
            return page

        print("ユーザー登録あり")
        # パスワードチェック
        if _user['password'] != password:  
            print(f"Password Error: {str(e)}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "Invalid credentials": str(e)},status_code=400)        
        
        token2 = request.cookies.get("token")
        print(f"- すでに持っているtoken2 JWT: {token2}")
        # しかしデバッグでは持てていない
        if token2 is None:
            print("token2なし")
            # token再生成する
            token2 = create_jwt(_user['user_id'], password)
        
        
        # 権限を判定する
        permission_str = request.cookies.get("permission")
        print(f"- 権限: {permission_str}です")
        if permission_str is None:
            print("権限なし")
            if _user['permission'] is None:
                print("権限なし")
                return templates.TemplateResponse(
                    "error.html", {"request": request, "error": "権限がありません"})
        else:
            print("DBにある権限は: " + str(_user['permission']))
            permission = _user['permission']
            print(permission)
            
        if permission == 2:
            print("shop権限あり /todayへ")
            redirect_response = RedirectResponse(url="/today")
            redirect_response.set_cookie(key="permission", value=str(2))
        else:
            print("shop権限なし")
            raise HTTPException(status_code=403, detail="Not Authorized")
        return redirect_response

        
    except Exception as e: 
        print(f"Error: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)})


# tokenを持っている場合
@app.get("/regist_complete", response_class=HTMLResponse, tags=["user"]) 
async def regist_complete(
    request: Request): 
    print("regist_completeに来た")
    # もしCookieのpermission=2ならば、/todayにリダイレクト
    if request.cookies.get("permission") == "2":
        print("permission=2")
        
        # リダイレクトレスポンスを設定
        redirect_response = RedirectResponse(url="/today")
        redirect_response.set_cookie(key="permission", value=str(2))
    
    # クッキーを設定したレスポンスを返す
    return redirect_response
        #return RedirectResponse(url="/today")
    
    return templates.TemplateResponse(
        "regist_complete.html",{"request": request})

# cookieを削除してログアウト
@app.get("/clear")
def clear_cookie():
    init_database()
    response = RedirectResponse(url="/")
    response.delete_cookie("token")
    response.delete_cookie("permission")
    return response

# お弁当屋の注文確認
@app.post("/today", response_class=HTMLResponse, tags=["order"])
@app.get("/today", response_class=HTMLResponse, tags=["order"])
def shop_today_order(request: Request,
    hx_request: Optional[str] = Header(None)):
    # 権限チェック
    permission = request.cookies.get("permission")
    print(permission)
    print("/todayに来た前")
    if permission != "2":
        raise HTTPException(status_code=403, detail="Not Authorized")
    print("/today成功")
    
    # 昨日の全注文
    print('orders開始')
    orders = select_today_orders(1) # mock_db_module.pyの120へ 
    # ここで取れていない!
    print('orders終了')
    print("orderのクラスは " + str(type(orders)))
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
