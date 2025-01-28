from fastapi import FastAPI, Form, Header, Response, HTTPException
import requests
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from functools import wraps
from pprint import pprint
from typing import Optional
import json
import logging


from local_jwt_module import TokenExpiredException, create_jwt, create_payload, verify_jwt
from mock_db_module import init_database, insert_order, insert_user, select_user, select_today_orders, update_user, delete_database

import tracemalloc

# tracemallocを有効にする
tracemalloc.start()


ALGORITHM = "HS256"

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# テストデータ作成
#delete_database()
#init_database()

@app.exception_handler(StarletteHTTPException) 
def http_exception_handler(request, exc): 
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)

# ログ用の設定
logging.basicConfig(level=logging.INFO)

# カスタムデコレーターを定義
def log_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info("- %s 前", func.__name__)
        result = func(*args, **kwargs)
        logging.info("- %s 後", func.__name__)
        return result
    return wrapper

# -----------------------------------------------------
# 新規ユーザーの登録
@log_decorator
def insert_new_user(userid, password, name):
    default_shop_id = "shop01"
    insert_user(userid, password, name, shop_id=default_shop_id, menu_id= 1, permission=1)
            
# tokenの再作成
#@log_decorator
async def update_token_and_exp(userid, password):
    try:
        payload = await create_payload(userid, password)
        exp = payload["exp"]
        print(f"exp: {exp}")
        update_user(userid, "expire_date", exp)

        token = await create_jwt(payload)
        update_user(userid, "token", token)
    except  Exception as e:
        print(f"Error: {str(e)}")
    return {"token": token, "exp": exp}

# ヘッダーを動的に設定
@log_decorator
def send_request(url, userid, token, exp, permission):
    # URLやその他の値を定義
    '''
    url = "http://localhost:8000/order_confirmed"
    current_permission = "1"
    userid = "user1"
    token = "your_token_here"
    exp = "your_exp_here"
    '''
    url_base_string = "http://127.0.0.1:8000"
    headers = {
    "Cookie": f"user_id={userid}; token={token}; exp={exp}; permission={permission};"
}
    print(f"headers: {headers}")
    print(url_base_string + url)
    response = requests.get(url_base_string + url, headers=headers, timeout=10)
    return response

# -----------------------------------------------------
# エントリポイント
@log_decorator
@app.get("/", response_class=HTMLResponse, tags=["user"])
def root(request: Request, response: Response):
    try:
        token = request.cookies.get("token") 
        permission = request.cookies.get("permission")
        # トークンが存在しない場合
        if token is None: 
            print("tokenはありません")
            print(token)

            return templates.TemplateResponse("login.html", {"request": request})
        else:
            # トークンが存在する場合
            print("tokenがあります")
            print(token)
            return templates.TemplateResponse(
            "protected_page.html", {"request": request, "permission": permission}
        )
    except Exception as e:
        print(f"Error: {str(e)}") 
        return RedirectResponse(url="/login")

# ログイン画面
# 表示するエンドポイント
@log_decorator
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ログイン処理
@log_decorator
@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request, response: Response,
    userid: str = Form(...),
    password: str = Form(...),
    name: str = Form(...)
):
    try:
        print(f"login input is {userid}")
        _user = select_user(userid)
        
        current_permission = 1
        if _user is None:
            print("ユーザーなし")
            insert_new_user(userid, password, name)
            _user = select_user(userid)
            current_permission = 1
        elif userid == _user['user_id'] and password == _user['password']:
            print("ユーザーあり")
            print(f"permission: {_user['permission']}")
            current_permission = _user['permission']
            
        else:
            print("ユーザーあり、パスワード不一致")
            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Invalid credentials"}
            )
            
        # tokenがない場合 
        # ユーザーなしなのに_user['token']がある場合は、tokenが消えている  
        if _user is not None and 'token' in _user and 'exp' in _user:
            token = _user['token']
            exp = _user["exp"]
        else:
            tx = await update_token_and_exp(userid, password)
            token = tx["token"]
            exp = tx["exp"]
        
        print(f" userid: {userid}")
        print(f" password: {password}")
        print(f" name: {name}")
        print(f" token: {token}")
        print(f" exp: {exp}")
        print(f" permission: {current_permission}")
        print(" current_permission: " + str(current_permission))
        print("  type: " + str(type(current_permission)))
 
        if current_permission == 2:
            print("/today - permission: 2")
            response = send_request("/today", userid, token, exp,current_permission)
            print(f"response: {response}")

        if current_permission == 3:
            response = send_request("/admin", userid, token, exp,current_permission)
        else:
            print("/order_confirmed.html - permission: 1")
            response = send_request("/order_confirmed", userid, token, exp, current_permission)
        
        print("")
        pprint(f"/login last is userid: {userid}, password: {password}, name: {name}, permission: {current_permission}")
        return responseHTMLResponse(content=response.text)
    
    except KeyError as e:
        print(f"/login KeyError: {e}")
        return templates.TemplateResponse(
            "login.html", {"request": request, "response": response, "error": "Invalid credentials"}
            )
    except Exception as e:
        print(f"/login Error: {str(e)}")
        return templates.TemplateResponse(
            "login.html", {"request": request, "response": response, "error": "Invalid credentials"}
            )
# -----------------------------------------------------
# tokenの状態をチェック
@log_decorator
def token_checker(request: Request):
    try:
        token = request.cookies.get("token")
        if token is None:
            print(f"Token is valid. Token: {token}")
            return False        
        
        payload = verify_jwt(token)
        if payload is None:
            print(f"Token is valid. Payload: {payload}")
            return False
                    
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
            #raise TokenExpiredException()                
            return False
        if expire_date < datetime.now():
            print("Token has expired.")
            #raise TokenExpiredException()
            return False
        print(f"Expire Date: {expire_date}")

        print("token is OK")
        return True
    except TokenExpiredException as e:
        print(f"TokenExpiredException: {str(e)}")


# tokenがある場合
'''
@log_decorator
@app.get("/protected_page", response_class=HTMLResponse, tags=["user"])
def protect_token(request: Request, response: Response):
    try:
        user_id = request.cookies.get(key="user_id")
        token = request.cookies.get(key="token")
        permission = request.cookies.get(key="permission")

        response.set_cookie(key="user_id", value=user_id['user_id'])
        response.set_cookie(key="token", value="valid_token")
        response.set_cookie(key="permission", value=permission)

        pprint(f"user_id: {user_id}, token: {token}, permission: {permission}")
        
        if permission == "2":
            response = RedirectResponse(url="/today",status_code=303)
        elif permission == "3":
            response = RedirectResponse(url="/admin",status_code=303)
        else:
            print("/order_confirmed.html - permission: 1")
            response = RedirectResponse(url="/order_confirmed",status_code=303) 
        
        return response
    
    except Exception as e:
        print(f"Error: {str(e)}") 
        return RedirectResponse(url="/login")
'''
    
# 注文確定
@log_decorator
@app.get("/order_confirmed", response_class=HTMLResponse)
def order_confirmed(request: Request, response: Response):
    try:
        print("ここまでいった order_confirmed")
        #permission = request.cookies.get("permission")
        #print(f"permission: {request.cookies.get("permission")}")
        #print(f"permission: {permission}")
        cookies = request.headers.get("cookie")
        permission = None
        user_id = None

        if cookies:
            # クッキーを解析
            for cookie in cookies.split("; "):
                key, value = cookie.split("=")
                if key == "permission":
                    permission = value
                elif key == "user_id":
                    user_id = value

        print(f"permission: {permission}")
        print(f"user_id: {user_id}")

        if permission == "1" and user_id:
            #user_id = request.cookies.get("user_id")
            #print(f"user_id: {user_id}")
            
            current_user = select_user(user_id)
            if current_user is None:
                return templates.TemplateResponse("login.html", {"request": request})
            
            # insert_order(shop_id, menu_id, company_id, user_id, amount)
            company_id = current_user['company_id']
            shop_id = current_user['shop_id']
            menu_id = current_user['menu_id']
            amount = 1
            print(f"company_id: {company_id}, shop_id: {shop_id}, menu_id: {menu_id}, amount: {amount}")
            insert_order(shop_id, menu_id, company_id, user_id=user_id, amount=amount)
            
            page = templates.TemplateResponse(
                "regist_complete.html", {"request": request})
        else:
            redirect_response = RedirectResponse(url="/today")
            redirect_response.set_cookie(key="permission", value=permission)
            # pageに response.cookiesを追加
            #page.headers.raw.extend(response.headers.raw)
            page = redirect_response
            
        return page

    except Exception as e: 
            print(f"Error: {str(e)}")
            return templates.TemplateResponse(
                "error.html", {"request": request, "error": str(e)})


# お弁当の注文完了　ユーザーのみ
@log_decorator
@app.get("/regist_complete", response_class=HTMLResponse, tags=["user"]) 
def regist_complete(): 
    return """<html><head><title>Complete</title></head><body><h1>お弁当の注文が完了しました。</h1></body></html>"""


# cookieを削除してログアウト
@log_decorator
@app.get("/clear")
def clear_cookie():
    delete_database()
    init_database()
    response = RedirectResponse(url="/")
    response.delete_cookie("token")
    response.delete_cookie("permission")
    return response

# お弁当屋の注文確認
@log_decorator
#@app.post("/today", response_class=HTMLResponse, tags=["order"])
@app.get("/today", response_class=HTMLResponse, tags=["order"])
def shop_today_order(request: Request,
    hx_request: Optional[str] = Header(None)):
    # 権限チェック
    permission = request.cookies.get("permission")
    print(permission)
    #print("/todayに来た前")
    #if permission != "1":
    #    raise HTTPException(status_code=403, detail="Not Authorized")
    print("/today成功")
    
    # 昨日の全注文
    print('orders開始')
    orders = select_today_orders('shop01') # mock_db_module.pyの120へ 
    #print(f"orders: {orders}")
    # ここで取れていない!
    #print('orders終了')
    #print("orderのクラスは " + str(type(orders)))
    '''
    if orders is None:
        print('ordersなし')
    else:
        print(orders)
    '''
    orders_list = json.loads(orders)
    print(f"orders_list: {orders_list}")
    context = {'request': request, 'orders': orders_list}
    #print(f"Context: {context}")
    if hx_request:
        return templates.TemplateResponse("table.html",context)

# 管理者画面
@log_decorator
@app.get("/admin", response_class=HTMLResponse, tags=["user"])
def admin(request: Request,
    hx_request: Optional[str] = Header(None)):
    # 権限チェック
    permission = request.cookies.get("permission")
    print(permission)
    if permission != "2":
        raise HTTPException(status_code=403, detail="Not Authorized")
    else:
        return templates.TemplateResponse(
            "admin.html", {"request": request})

    
# ブラウザが要求するfaviconのエラーを防ぐ
# https://github.com/fastapi/fastapi/discussions/11385
favicon_path = './static/favicon.ico'  # Adjust path to file

# Ensure favicon.ico is accessible
@app.get('/favicon.ico', include_in_schema=False)
def favicon():
     return FileResponse(favicon_path)
 
# Mount the directory where favicon.ico is located 
# faviconのマウント
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# 他のモジュールでの誤使用を防ぐ
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, timeout_keep_alive=100)
