from fastapi import Depends, FastAPI, Form, HTTPException, Header, Query , Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from datetime import datetime, timedelta
from typing import Union # 型ヒント用モジュール
from fastapi.templating import Jinja2Templates # HTMLテンプレート
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from local_jwt_module import create_jwt, verify_jwt, sign_message # type: ignore


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

@app.exception_handler(StarletteHTTPException) 
async def http_exception_handler(request, exc): 
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)

# 登録完了画面 https://127.0.0.1:8000でアクセスする
@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    try:
        # Cookieを設定
        #response.set_cookie(key="my_cookie", value="cookie_value") # OK 

        # もしIDがなければIDを発行する
        id = "1"
        formatted_id = str(id).zfill(3)
        response.set_cookie(key="id", value=str(formatted_id))
        print(f"- Cookie id: 001")
        
        today_date = datetime.today()
        today_date_str = datetime.today().strftime('%Y-%m-%d') 
        print(f"- regist_date: {today_date_str}")
        
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
            #max_age=timedelta(days=days_valid).total_seconds(),
            max_age=timedelta(seconds=30).total_seconds(),
            )
        print(f"- Generated JWT: {token}")
        
        expire_date = today_date + timedelta(days=days_valid)
        
        expire_date_str = expire_date.strftime('%Y-%m-%d %H:%M:%S') 
        print(f"- expire_date: {expire_date_str}")


        page = templates.TemplateResponse(
            "regist_complete.html", {"request": request, "token": token})
        
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
    return templates.TemplateResponse(
        "confirm_token.html",{"request": request})
# tokenが期限切れの場合は不明。

# https://fastapi.tiangolo.com/ja/tutorial/dependencies/dependencies-in-path-operation-decorators/#path-operationdependencies
async def verify_token(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")
    
async def verify_key(x_key: str = Header()):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


# /abcを加えた場合    
@app.get("/check", response_class=HTMLResponse)
async def read_abc(
    request: Request, token: str = Query(...)):
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

# @app.get("/get-cookie") 
# def get_cookie(response: Response): 
@app.get("/check-token", dependencies=[Depends(verify_token)])
def check_token(): 
    response = Response()
    response.headers["X-Custom-Header"] = "CustomValue"
    response.headers["Set-Cookie"] = "sessionId=12345"
    response.body = b"Hello, World!"
    # ここで設定されたCookieを確認する 
    print(response.headers) 
    print(response.body) 
    #return {"message": "Check the response headers in logs"}
    return JSONResponse(
        content={"message": "Check the response headers in logs"})
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
