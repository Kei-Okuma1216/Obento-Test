from functools import wraps
import logging
from fastapi import FastAPI, Form, Header, Response, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from http.cookies import SimpleCookie
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from typing import Optional

from local_jwt_module import TokenExpiredException, create_jwt, verify_jwt
from mock_db_module import init_database, insert_order, insert_user, select_user, select_today_orders, update_user, delete_database

import tracemalloc

# tracemallocを有効にする
tracemalloc.start()


ALGORITHM = "HS256"

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# テストデータ作成
#delete_database()
init_database()

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

# -----------------------------------------------------
# エントリポイント
@app.get("/", response_class=HTMLResponse, tags=["user"])
@log_decorator
async def root(request: Request, response: Response):
    try:
        token = request.cookies.get("token") 
        print(token)
        # トークンが存在しない場合
        if token is None: 
            print("tokenはありません")
            return templates.TemplateResponse("login.html", {"request": request})
        # トークンが存在する場合
        return templates.TemplateResponse(
            "protected_page.html", {"request": request, "permission": "2"}
        )
    except Exception as e:
        print(f"Error: {str(e)}") 
        return RedirectResponse(url="/login")

# -----------------------------------------------------
# ログイン画面を表示するエンドポイント
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ログイン処理用エンドポイント
@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,response: Response,
    userid: str = Form(...),
    password: str = Form(...),
    name: str = Form(...)
    ):

    _user = await select_user(userid)
    if _user is None:
        print("ユーザーなし")
        await insert_user(userid, password, name, shop_id=1, menu_id= 1, permission=1)

        token = create_jwt(userid, password)
        
        response.set_cookie(key="user_id", value=userid)
        response.set_cookie(key="token", value=token)
        response.set_cookie(key="permission", value="1")
        
        await update_user(userid, token)
        
        return templates.TemplateResponse(
            "login.html", {"request": request, "response": response, "error": "Invalid credentials"})

    if userid == _user['user_id'] and password == _user['password']:  
        print("ユーザーあり")
        # サンプルの認証ロジック
        response.set_cookie(key="user_id", value=_user['user_id'])
        token = request.cookies.get("token")
        response.set_cookie(key="token", value=token)
        response.set_cookie(key="permission", value=_user['permission'])
        response = RedirectResponse(url="/protected_page", status_code=303)

        return response
    else:
        print("ユーザー認証失敗")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

# -----------------------------------------------------
# tokenがある場合
@app.get("/protected_page", response_class=HTMLResponse, tags=["user"])
@log_decorator
async def protect_token(request: Request, response: Response):
    try:
        user_id = request.get_cookie(key="user_id")
        token = request.get_cookie(key="token")
        permission = request.get_cookie(key="permission")

        response.set_cookie(key="user_id", value=user_id['user_id'])
        response.set_cookie(key="token", value="valid_token")
        response.set_cookie(key="permission", value=permission)

        if permission == "2":
            response = RedirectResponse(url="/today",status_code=303)
        else:
            response = RedirectResponse(url="/order_confirmed",status_code=303) 
        
        # tokenの状態をlogでチェック
        token = request.cookies.get("token")
        if token is None:
            print(f"Token is valid. Token: {token}")
            return RedirectResponse(url="/login")
        
        payload = verify_jwt(token)
        if payload is None:
            print(f"Token is valid. Payload: {payload}")
            return RedirectResponse(url="/login")
            
        print(payload)
        
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

        return response
    
    except Exception as e:
        print(f"Error: {str(e)}") 
        return RedirectResponse(url="/login")
    
# 注文確定
@app.post("/order_confirmed", response_class=HTMLResponse, tags=["user"])
async def order_confirmed(request: Request, response: Response):
    try:
        permission = response.get_cookie(key="permission")
        if permission == "1":
            user_id = response.get_cookie(key="user_id")
            current_user = await select_user(user_id)
            if current_user is None:
                return templates.TemplateResponse("login.html", {"request": request})
            
            # insert_order(shop_id, menu_id, company_id, user_id, amount)
            shop_id = current_user['shop_id']
            menu_id = current_user['menu_id']
            company_id = current_user['company_id']
            amount = 1
            await insert_order(shop_id, menu_id, company_id, user_id=user_id, amount=amount)
            
            print("order_item 1件登録した")
            page = templates.TemplateResponse(
                "regist_complete.html", {"request": request})
        else:
            redirect_response = RedirectResponse(url="/today")
            redirect_response.set_cookie(key="permission", value=permission)
            # pageに response.cookiesを追加
            page.headers.raw.extend(response.headers.raw)
            
        return page

    except Exception as e: 
            print(f"Error: {str(e)}")
            return templates.TemplateResponse(
                "error.html", {"request": request, "error": str(e)})


# お弁当の注文完了　ユーザーのみ
@app.get("/regist_complete", response_class=HTMLResponse, tags=["user"]) 
async def regist_complete(): 
    return """<html><head><title>Complete</title></head><body><h1>お弁当の注文が完了しました。</h1></body></html>"""


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
async def shop_today_order(request: Request,
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
    orders = await select_today_orders(1) # mock_db_module.pyの120へ 
    # ここで取れていない!
    print('orders終了')
    print("orderのクラスは " + str(type(orders)))
    if orders is None:
        print('ordersなし')
    else:
        print(orders)
   
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
