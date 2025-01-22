from contextlib import asynccontextmanager
from http.cookiejar import Cookie
import sqlite3
from fastapi import Cookie, FastAPI, Form, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from datetime import datetime
from typing import Union # 型ヒント用モジュール
from fastapi.templating import Jinja2Templates # HTMLテンプレート
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from local_jwt_module import create_jwt, verify_jwt
ALGORITHM = "HS256"
import sys 
print(sys.path)
from init_module import init_database, insert_mock_user, get_connection, select_mock_user, select_mock_user

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@asynccontextmanager 
async def lifespan(app: FastAPI): 
    # 起動時に実行する処理をここに記述 
    print("FastAPIアプリケーションが起動しました！") 
    init_database()    

    yield 
    # 終了時に実行する処理をここに記述 
    print("FastAPIアプリケーションが終了します！") 
    app.router.lifespan_context = lifespan

@app.exception_handler(StarletteHTTPException) 
async def http_exception_handler(request, exc): 
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)



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
        return templates.TemplateResponse("login.html", {"request": request})

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
    request: Request, response: Response, userid: str = Form(...), password: str = Form(...)):

    try:
        # ユーザー登録
        conn = get_connection()
        result = select_mock_user(conn, userid)
        print(result)
        if  result is None:
            # ユーザーなし
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
            # ユーザーあり
            #print(result['userid'])
            #print(result['password'])
            if result[1] == password:  # パスワードチェック
                return templates.TemplateResponse(       "regist_complete.html",
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
                "token_error.html", {"request": request, "error": "Token is missing"}, status_code=400)
                     
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

# ----------------------------------

#global conn
def init_database():
    
    try:
          conn = sqlite3.connect('example.db')
          if conn is None: 
               print("データベース接続の確立に失敗しました。")
          else:
               cursor = conn.cursor()
               create_user_table(cursor) 
               insert_mock_user(conn, "k.okuma", "aaa", "", 1)
               insert_mock_user(conn, "k.okuma@ten-system.com", "aaa12345", "", 3)
               print('A'+ str(conn))
               conn.close() 
               print("データベースファイル 'sample.db' が正常に作成されました。")
    except sqlite3.Error as e: 
         print(f"SQLiteエラー: {e}")
    except Exception as e: 
        print(f"Error: {str(e)}")
        import traceback 
        traceback.print_exc()
     
# テーブルを作成
def create_user_table(cursor):
     cursor.execute('''
     CREATE TABLE User (
     userid TEXT PRIMARY KEY,
     password TEXT,
     token TEXT,
     permission INTEGER
     )
     ''')

# コネクションを閉じる（実際のテストでは不要）
#conn.close()

def get_connection(): 
     conn = sqlite3.connect('example.db') 
     # データベースファイル名を指定 
     return conn

# テスト用の偽ユーザーを追加する関数
def insert_mock_user(conn, userid, password, permission):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO User (userid, password, permission)
    VALUES (?, ?, ?)
    ''', (userid, password, permission))
    conn.commit()
    conn.close()


def select_mock_user(conn, userid):
     conn = get_connection()
     cursor = conn.cursor()
     print("手前")
     result = cursor.execute('SELECT * FROM User')
     print("後")
     conn.close()
     if result[userid] is None:
          return None
     else:
          return result[userid]

# データの確認
def show_all_users(cursor):
     conn = get_connection()
     cursor = conn.cursor()
     cursor.execute('SELECT * FROM User')
     rows = cursor.fetchall()
     for row in rows:
          print(row)
     conn.close()