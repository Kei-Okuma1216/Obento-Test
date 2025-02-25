import asyncio
import json
import pprint
from fastapi import Depends, FastAPI, Form, Header, Query, Response, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse,  RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
import tracemalloc
from typing import Optional
import urllib.parse

import jwt

from local_jwt_module import SECRET_KEY, TokenExpiredException, get_new_token, check_cookie_token

from sqlite_database import init_database, insert_new_user, insert_order, select_company_order, select_shop_order, select_user, show_all_orders, update_user
from schemas import User
#from .schemas.schemas import User
from utils import get_exp_value, stop_twice_order, compare_expire_date, delete_all_cookies, get_all_cookies, log_decorator, prevent_order_twice, set_all_cookies
# tracemallocを有効にする
tracemalloc.start()

ALGORITHM = "HS256"

app = FastAPI()
templates = Jinja2Templates(directory="templates")
from fastapi.staticfiles import StaticFiles

#app.mount("/static", StaticFiles(directory="static"), name="static")

# login.htmlに戻る
def redirect_login(request: Request, message: str):
    return templates.TemplateResponse("login.html", {"request": request, "message": message})

# 例外ハンドラーの設定
@app.exception_handler(TokenExpiredException)
async def token_expired_exception_handler(request: Request, exc: TokenExpiredException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )
# -----------------------------------------------------
# エントリポイント
@app.get("/", response_class=HTMLResponse)
@log_decorator
async def root(request: Request, response: Response):

    # テストデータ作成
    #await init_database()

    if(stop_twice_order(request)):
        last_order = request.cookies.get('last_order_date')
        
        message = f"<html><p>きょう２度目の注文です。</p><a>last order: {last_order} </a><a href='https://127.0.0.1:8000/clear'>Cookieを消去</a></html>"

        return HTMLResponse(message)


    # token チェックの結果を取得
    token_result = check_cookie_token(request)
    print(f"token_result: {token_result}")

    if token_result is None:
        print("token_result: ありません")
        message = "token の有効期限が切れています。再登録をしてください。"
        return templates.TemplateResponse("login.html", {"request": request, "message": message})

    # もし token_result がタプルでなければ（＝TemplateResponse が返されているなら）、そのまま返す
    if not isinstance(token_result, tuple):
        return token_result
    else:
        token, exp = token_result

    try:
        if compare_expire_date(exp):
            return redirect_login(request, "tokenの有効期限が切れています。再登録をしてください。")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        #print(f"jwt.decode: {payload}")
        username = payload['sub']
        permission = payload['permission']
        exp = payload['exp']
        print(f"exp: {exp}")
        print("token is not expired.")

        # 毎回tokenを作り直す
        response = RedirectResponse(url="/order_complete", status_code=303)
        
        data = {
            "sub": username,
            "permission": permission,
        }
        access_token, exp = get_new_token(data)
        new_data = {
            "sub": username,
            "permission": permission,
            "exp": exp,
            "token": access_token
        }

        set_all_cookies(response, new_data)

        return response

    except jwt.ExpiredSignatureError:
        message = "トークンの有効期限が切れています。再登録をしてください。"
        return redirect_login(request, message)

    except jwt.InvalidTokenError:
        message = "無効なトークンです"
        return redirect_login(request, message)   


# ログイン画面を表示するエンドポイント
@app.get("/login", response_class=HTMLResponse)
@log_decorator
async def login_get(request: Request, message: Optional[str] = ""):
    try:
        print("/login")
        redirect_login(request, "ようこそ")

    except Exception as e:
        print(f"login_get Error: {str(e)}")
        encoded_message = urllib.parse.quote("ログインページが表示できません")
        redirect_url = f"/login.html?message={encoded_message}"
        response = RedirectResponse(url=redirect_url, status_code=303)
        
        return response
# -----------------------------------------------------
# ログイン認証
@log_decorator
async def authenticate_user(request: Request, username, password) -> Optional[User]:
    try:
        user = await select_user(username)
        #print(f"type: {str(type(user))}")
        #print(f"name: {user.name}")

        if user is None:
            #print(f"username: {user.username}")
            await insert_new_user(username, password, 'name')
            user = await select_user(username)

        if user.get_password() != password:
            return None

        data = {
            "sub": user.get_username(),
            "permission": user.get_permission()
        }
        access_token, utc_dt_str = get_new_token(data)
        
        user.set_token(access_token)
        #print(f"access_token: {access_token}")
        user.set_exp(utc_dt_str)
        #print(f"expires: {utc_dt_str}")
        #print(f"user: {user}")
        return user

    except HTTPException as e:
        print(f"/login HTTPエラー: {e.detail}")
        return templates.TemplateResponse("login.html", {"request": request, "message": e.detail})
    except Exception as e:
        print(f"認証エラー: {e}")
        return templates.TemplateResponse("login.html", {"request": request, "message": "予期せぬエラーが発生しました。"})

# ログインPOST
@app.post("/login", response_class=HTMLResponse)
@log_decorator
async def login_post(request: Request, response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        #form = await request.form()
        username = form_data.username
        password = form_data.password

        user = await authenticate_user(request, username, password) 
        #print(f"user: {user}")
        if user is None:
            raise HTTPException(status_code=400, detail="ログインに失敗しました。")

        print("username と password一致")

        # リダイレクト前
        permission = user.get_permission()

        redirect_url = {1: "/order_complete", 2: "/manager", 10: "/today", 99: "/admin"}.get(permission, "/error")
        #print(f"redirect_url: {redirect_url}")

        response = RedirectResponse(
            url=redirect_url, status_code=303)

        #print("ここまできた 1")
        data = {
            'sub': user.get_username(),
            'token': user.get_token(),
            'exp': user.get_exp(),
            'permission': user.get_permission()
        }
        print(f" 'sub': {user.get_username()}")
        print(f" 'token': {user.get_token()}")
        print(f" 'exp': {user.get_exp()}")
        print(f" 'permission': {user.get_permission()}")


        set_all_cookies(response, data)

        #user.print_max_age_str()
        
        # トークンのsave
        username = user.get_username()
        await update_user(username, "token", user.get_token())
        await update_user(username, "exp", user.get_exp())

        return response
    
    except HTTPException as e:
        print(f"/login_post HTTPエラー: {e.detail}")
        encoded_message = urllib.parse.quote(e.detail)
        return RedirectResponse(url=f"/login?message={encoded_message}", status_code=303)

    except Exception as e:
        print(f"/login 予期せぬエラー: {e}")
        encoded_message = urllib.parse.quote("予期せぬエラーが発生しました。")
        return RedirectResponse(url=f"/login?message={encoded_message}", status_code=303)


# お弁当の注文完了　ユーザーのみ
@app.get("/order_complete",response_class=HTMLResponse) 
@log_decorator
async def regist_complete(request: Request, response: Response,
                    hx_request: Optional[str] = Header(None)): 
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        username = cookies['sub']

        # 注文追加
        user = await select_user(username)

        if user is None:
            print(f"user:{user} 取得に失敗しました")
            return HTMLResponse("<html><p>user 取得に失敗しました</p></html>")
    
        await insert_order(
            user.company_id,
            user.username,
            user.shop_name,
            user.menu_id,
            amount=1)

        orders = await select_shop_order(user.shop_name, -7, user.username)

        if orders is None or len(orders) == 0:
            print("No orders found or error occurred.")
            return HTMLResponse("<html><p>注文が見つかりません。</p></html>")

        #orders.sort()
        await show_all_orders()
        
        return await order_table_view(request, response, orders, "order_complete.html")

                
        # 日時で逆順
        orders.sort(key=lambda x: x.created_at, reverse=True)

        context = {'request': request, 'orders': orders}

        if hx_request:
            '''templates.TemplateResponse() は デフォルトでは Response を新しく作成する ため、response.set_cookie() の影響を受けない場合がある。'''
            return templates.TemplateResponse("table.html", context)

        last_order_date = orders[0].created_at
        prevent_order_twice(response, last_order_date)

        context = {'request': request, 'orders': orders}
        template_response = templates.TemplateResponse("order_complete.html", context)
        template_response.headers["Set-Cookie"] = response.headers.get("Set-Cookie")

        #print("1.Cookie Value")
        #print(template_response.headers["Set-Cookie"])
        #print("2. max_age value")
        header = template_response.headers["Set-Cookie"]
        exp_value = get_exp_value(header)
        print(f"exp_value: {exp_value}")


        return template_response

    except Exception as e:
        orders = []
        print(f"/order_complete Error: {str(e)}")
        return HTMLResponse(f"<html><p>エラーが発生しました: {str(e)}</p></html>")


# cookieを削除してログアウト
@app.get("/clear")
@log_decorator
async def clear_cookie(response: Response):
    response = RedirectResponse(url="/")
    delete_all_cookies(response)

    return response

# お店の権限チェック
#@log_decorator
def check_store_permission(request: Request):
    permission = request.cookies.get("permission")
    #print(f"check_store_permission: {permission}")
    if permission is None:
        raise HTTPException(status_code=403, detail="Permission Data is not Contained")
    if permission == "1":
        raise HTTPException(status_code=403, detail="Not Authorized")

# お弁当屋の注文確認
@app.post("/today", response_class=HTMLResponse, tags=["order"])
@app.get("/today", response_class=HTMLResponse, tags=["order"])
@log_decorator
async def shop_today_order(request: Request, response: Response, hx_request: Optional[str] = Header(None)):
    
    try:
        check_store_permission(request)

        cookies = get_all_cookies(request)
        if not cookies:
            print('cookie userなし')
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)
        
        # 昨日の全注文
        orders = await select_shop_order('shop01')
        
        if orders is None:
            print('ordersなし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")
        
        print(f"ordersあり")
        # ソート結果を確認
        #for order in orders:
            #print(order)
        return await order_table_view(request, response, orders, "store_orders_today.html")

        #await order_table_view(request, response, orders, "store_orders_today.html")
        '''
        # ordersリストをin-placeで降順にソート
        orders.sort(key=lambda x: x.created_at, reverse=True)
    
        context = {'request': request, 'orders': orders}
        if hx_request:
            return templates.TemplateResponse(
                "table.html",context)

        template_response = templates.TemplateResponse(
            "store_orders_today.html", context)

        # Set-CookieヘッダーがNoneでないことを確認
        set_cookie_header = response.headers.get("Set-Cookie")
        if set_cookie_header is not None:
            template_response.headers["Set-Cookie"] = set_cookie_header

        return template_response
'''
    except Exception as e:
        print(f"/shop_today_order Error: {str(e)}")
        return HTMLResponse(f"<html><p>エラーが発生しました: {str(e)}</p></html>")

# 注文一覧テーブル表示
@log_decorator
async def order_table_view(request: Request, response: Response, orders, redirect_url: str, hx_request: Optional[str] = Header(None)):
    #"store_orders_today.html"
    try:        
        # ordersリストをin-placeで降順にソート
        orders.sort(key=lambda x: x.created_at, reverse=True)
        #print("ここまできた 1")
        context = {'request': request, 'orders': orders}
        #if hx_request:
        #    return templates.TemplateResponse(
        #        "table.html",context)
        templates.TemplateResponse("table.html",context)
        #print("ここまできた 2")
        template_response = templates.TemplateResponse(
            redirect_url, context)
        #print("ここまできた 3")
        # Set-CookieヘッダーがNoneでないことを確認
        set_cookie_header = response.headers.get("Set-Cookie")
        #print("ここまできた 4")
        if set_cookie_header is not None:
            template_response.headers["Set-Cookie"] = set_cookie_header
        #print("ここまできた 5")
        return template_response
    except Exception as e:
        print(f"/order_table_view Error: {str(e)}")
        return JSONResponse({"message": "エラーが発生しました"}, status_code=404)

# 注文情報を取得する
# 例 /order_json?days_ago=-5
@app.get("/order_json",response_class=HTMLResponse) 
@log_decorator
async def order_json(request: Request, days_ago: str = Query(None)): 
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            #return HTMLResponse("<html><p>ユーザー情報が取得できませんでした。</p></html>")
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        # 注文追加
        user = await select_user(cookies['sub'])

        if user is None:
            print(f"user:{user} 取得に失敗しました")
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        if days_ago is not None:
            print(f"days_ago: {int(days_ago)}")

        #print(f"days_ago: {days_ago}")
        # 履歴取得
        if days_ago is None:
            print("全履歴を取得する") 
            orders = await select_shop_order(user.shop_name)
        elif days_ago.isdigit() or (days_ago.startswith('-') and days_ago[1:].isdigit()):
            print(f"{days_ago} 日前までの履歴を取得する")
            orders = await select_shop_order(user.shop_name, days_ago)
        else:
            return JSONResponse({"error": "days_ago の値が無効です"}, status_code=400)

        if not orders:
            print("No orders found or error occurred.")
            return JSONResponse({"message": "注文が見つかりません。"}, status_code=404)

        # 日時で逆順
        orders.sort(key=lambda x: x.created_at, reverse=True)

        #print("ここまできた 3")
        for order in orders:
            print(order.model_dump_json())

        #print("ここまできた 4")
        #orders = [dict(order) for order in orders]  # 明示的に辞書のリストに変換

        #orders_dict = [order.model_dump() for order in orders]
        #orders_json = json.dumps(orders_dict, indent=4, default=str)
        #print(orders_json)
        #return HTMLResponse(orders_json)
        #return JSONResponse(content=orders_dict)
        # datetime を JSON に変換可能な形式に変換
        orders_dict = [order.model_dump() for order in orders]
        orders_json = json.dumps(orders_dict, default=str)  # ← datetime を文字列に変換

        return JSONResponse(content=json.loads(orders_json))  # JSON をパースしてレスポンス
    
    except Exception as e:
        orders = []
        print(f"/order_complete Error: {str(e)}")
        return JSONResponse({"error": f"エラーが発生しました: {str(e)}"}, status_code=500)

# 管理者の権限チェック
def check_admin_permission(request: Request):
    permission = request.cookies.get("permission")
    print(f"permission: {permission}")
    if permission != "3":
        raise HTTPException(status_code=403, detail="Not Authorized")

# 管理者画面
@app.get("/admin", response_class=HTMLResponse)
@log_decorator
def admin_view(request: Request):    
    
    # 権限チェック
    check_admin_permission(request)
    
    return templates.TemplateResponse(
        "admin.html", {"request": request})

# 会社お弁当担当者画面
@app.get("/manager", response_class=HTMLResponse)
@log_decorator
async def manager_view(request: Request, response: Response, hx_request: Optional[str] = Header(None)):
    try:
        #check_store_permission(request)

        cookies = get_all_cookies(request)
        if not cookies:
            print('cookie userなし')
            return JSONResponse({"error": "ユーザー情報が取得できませんでした。"}, status_code=400)

        # 昨日の全注文
        orders = await select_company_order(1)

        if orders is None:
            print('ordersなし')
            return HTMLResponse("<html><p>注文は0件です</p></html>")

        print(f"ordersあり")
        # ソート結果を確認
        #for order in orders:
            #print(order)

        # ordersリストをin-placeで降順にソート
        orders.sort(key=lambda x: x.created_at, reverse=True)

        context = {'request': request, 'orders': orders}
        if hx_request:
            return templates.TemplateResponse(
                "table.html",context)

        template_response = templates.TemplateResponse(
            "store_orders_today.html", context)

        # Set-CookieヘッダーがNoneでないことを確認
        set_cookie_header = response.headers.get("Set-Cookie")
        if set_cookie_header is not None:
            template_response.headers["Set-Cookie"] = set_cookie_header

        return template_response

    except Exception as e:
        print(f"/manager_view Error: {str(e)}")
        return HTMLResponse(f"<html><p>エラーが発生しました: {str(e)}</p></html>")

    
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
'''if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, timeout_keep_alive=100)
'''
if __name__ == "__main__":
    # イベントループの存在確認
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    #loop.run_until_complete(regist_complete())
    # 別のイベントループに切り替えてみる
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Uvicornサーバーの起動
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=100)