from fastapi import FastAPI, Form, Query , Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from datetime import datetime, timedelta
from typing import Union # 型ヒント用モジュール
from fastapi.templating import Jinja2Templates # HTMLテンプレート
from starlette.requests import Request

from jwt_module import create_jwt, verify_jwt, sign_message


app = FastAPI()
templates = Jinja2Templates(directory="templates")


# ユーザー登録ページ
@app.get("/", response_class=HTMLResponse) 
async def read_root(request: Request): 
    # もしtokenがついていたら、独自のページに遷移する。
    token = request.cookies.get("token") 
    if token: # Tokenがある場合は /cde にリダイレクト 
        return RedirectResponse(url="/cde")
    return templates.TemplateResponse("login.html", {"request": request})

"""
venv簡易実行マニュアル
0. OpenSSLで秘密鍵→CSR→自己署名証明書の順につくる
1. main.pyのあるディレクトリでcmdを押してエンターを押す
2. activateする
.\env\Scripts\activate
3. uvicornを使ってHTTPSサーバーを起動する
生成した証明書と秘密鍵を使用して、uvicornでHTTPSサーバーを起動します
uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt
4. ブラウザで、https://localhost:8000 にアクセスする
5. もしエラーになれば、詳細設定ボタン押下後、Localhostにすすむ（安全ではありません）のリンクをクリックする。 
"""
# 登録完了画面 https://127.0.0.1:8000でアクセスする
@app.post("/register", response_class=HTMLResponse)
async def register(
    #request: Request, username: str = Form(...), password: str = Form(...)):
    request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    try:
        # Cookieを設定
        #response.set_cookie(key="my_cookie", value="cookie_value") # OK 

        id = "1"
        formatted_id = str(id).zfill(3)
        response.set_cookie(key="id", value=str(formatted_id))
        print(f"Cookie id: 001")
        
        #today_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S') 
        today_date = datetime.today()
        today_date_str = datetime.today().strftime('%Y-%m-%d') 
        print(f"regist_date: {today_date_str}")
        
        response.set_cookie(
            key="regist_date",
            value=today_date_str
            )
        
        token = create_jwt(username, password, datetime.today())

        # 有効期間を日単位で設定
        days_valid = 3 
        response.set_cookie(
            key="token",
            value=token,
            max_age=timedelta(days=days_valid).total_seconds(),
            httponly=True
            )
        print(f"Generated JWT: {token}")
        
        expire_date = today_date + timedelta(days=days_valid)
        expire_date_str = expire_date.strftime('%Y-%m-%d %H:%M:%S') 
        print(f"expire_date: {expire_date_str}")


        page = templates.TemplateResponse(
            "regist_complete.html", {"request": request, "token": token})
        response.set_cookie(key="my_cookie", value="cookie_value") 
        
        # pageに response.cookiesを追加
        page.headers.raw.extend(response.headers.raw)
        
        return page

    except Exception as e: 
        print(f"Error: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)})

# Cookieにtokenがある場合、/cdeに遷移する    
@app.get("/cde", response_class=HTMLResponse) 
async def read_cde(request: Request): 
    return templates.TemplateResponse("cde.html",
                                      {"request": request})


# /abcを加えた場合    
@app.get("/abc", response_class=HTMLResponse)
async def read_abc(request: Request, token: str = Query(...)):
    try:
        payload = verify_jwt(token)
        if payload:
            print(f"Token is valid. Payload: {payload}")
            
            # 現在の日付
            cur_date = datetime.now()
            # 日付を取り出す 
            token_date = datetime.fromisoformat(payload["date"]) 
            print(f"Retrieved Date: {token_date}")
            
            # abc.html
            return templates.TemplateResponse("abc.html",
                {"request": request, "token": token,
                "retrieved_date": token_date, "current_date": cur_date})
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
    uvicorn.run(app, host="127.0.0.1", port=8000)
