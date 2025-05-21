# routers/log.py
'''
# 管理者ユーザー用
    1. list_logs():
    2. view_log(filename: str):
    3. list_order_logs():
    4. view_order_log(filename: str):
# 店舗ユーザー用
    5. filter_order_logs(background_tasks: BackgroundTasks, shop: str = Query(...)):
    6. list_combined_order_logs():
    7. view_combined_order_log(filename: str):
'''
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
import os

log_router = APIRouter(prefix="/api/v1", tags=["logs"])

LOG_DIR = "./logs"
ORDER_LOG_DIR = "./order_logs"


# 管理者ユーザー用
@log_router.get(
    "/log_html",
    response_class=HTMLResponse,
    summary="ログ一覧のHTML表示：管理者ユーザー",
    description="ログディレクトリ内のファイル一覧をHTMLリンクで表示します。"
)
def list_logs():
    if not os.path.exists(LOG_DIR):
        raise HTTPException(status_code=404, detail="ログディレクトリが存在しません")
    
    log_files = sorted(os.listdir(LOG_DIR), reverse=True)
    links = [f"<li><a href='/api/v1/log_html/{file}'>{file}</a></li>" for file in log_files]
    html = f"<h1>ログ一覧</h1><ul>{''.join(links)}</ul>"
    return HTMLResponse(content=html)
# @log_router.get("/log_html", response_class=HTMLResponse)
# def list_logs():
#     if not os.path.exists(LOG_DIR):
#         return "<h1>ログディレクトリが存在しません</h1>"
#     log_files = sorted(os.listdir(LOG_DIR), reverse=True)
#     links = [f"<li><a href='/api/v1/log_html/{file}'>{file}</a></li>" for file in log_files]
#     return f"<h1>ログ一覧</h1><ul>{''.join(links)}</ul>"

@log_router.get(
    "/log_html/{filename}",
    response_class=HTMLResponse,
    summary="ログファイル内容表示：管理者ユーザー",
    description="指定されたログファイルの内容をHTMLとして表示します。"
)
def view_log(filename: str):
    path = os.path.join(LOG_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="指定されたログファイルが見つかりません")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().replace("\n", "<br>")
        return HTMLResponse(content=f"<h1>{filename}</h1><pre>{content}</pre>")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル読み込み中にエラーが発生しました: {str(e)}")

# @log_router.get("/log_html/{filename}", response_class=HTMLResponse)
# def view_log(filename: str):
#     path = os.path.join(LOG_DIR, filename)
#     if os.path.exists(path):
#         with open(path, "r", encoding="utf-8") as f:
#             content = f.read().replace('\n', '<br>')
#         return f"<h1>{filename}</h1><pre>{content}</pre>"
#     else:
#         return HTMLResponse("ログファイルが存在しません。", status_code=404)

@log_router.get(
    "/order_log_html",
    response_class=HTMLResponse,
    summary="注文ログファイル一覧（HTML）：管理者ユーザー",
    description="`order_logs` ディレクトリ内にある注文ログファイルの一覧を HTML 形式で表示します。",
)
def list_order_logs():
    if not os.path.exists(ORDER_LOG_DIR):
        raise HTTPException(status_code=404, detail="注文ログディレクトリが存在しません")

    files = sorted(os.listdir(ORDER_LOG_DIR), reverse=True)
    links = [f"<li><a href='/api/v1/order_log_html/{f}'>{f}</a></li>" for f in files]
    html = f"<h1>注文ログ一覧</h1><ul>{''.join(links)}</ul>"
    return HTMLResponse(content=html)


@log_router.get(
    "/order_log_html/{filename}",
    response_class=HTMLResponse,
    summary="注文ログファイル表示：管理者ユーザー",
    description="指定された注文ログファイルの内容を HTML 形式で表示します。"
)
def view_order_log(filename: str):
    path = os.path.join(ORDER_LOG_DIR, filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="注文ログファイルが存在しません")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().replace("\n", "<br>")
        return HTMLResponse(content=f"<h1>{filename}</h1><pre>{content}</pre>")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイルの読み込み中にエラーが発生しました: {str(e)}")

# @log_router.get("/order_log_html/{filename}", response_class=HTMLResponse)
# def view_order_log(filename: str):
#     path = os.path.join(ORDER_LOG_DIR, filename)
#     try:
#         if os.path.exists(path):
#             with open(path, "r", encoding="utf-8") as f:
#                 content = f.read().replace('\n', '<br>')
#             return f"<h1>{filename}</h1><pre>{content}</pre>"
#         else:
#             return HTMLResponse("注文ログファイルが存在しません。", status_code=404)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import Query, BackgroundTasks
from fastapi.responses import JSONResponse

# 店舗ユーザー用
@log_router.get(
    "/filter_order_logs",
    summary="注文ログの抽出処理：店舗ユーザー",
    description="指定された店舗名に基づいて、注文ログを抽出します（バックグラウンド処理）。",
    tags=["logs"]
)
async def filter_order_logs(
    background_tasks: BackgroundTasks,
    shop: str = Query(..., description="対象店舗名")
):
    def run_log_filter():
        import subprocess
        subprocess.run(
            ["python", "order_log_filter_config.py", "order_logs", shop],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    background_tasks.add_task(run_log_filter)
    return {"message": "ログ抽出処理をバックグラウンドで開始しました"}

# @log_router.get("/filter_order_logs", tags=["logs"])
# async def filter_order_logs(background_tasks: BackgroundTasks, shop: str = Query(...)):
#     def run_log_filter():
#         import subprocess
#         subprocess.run(
#             ["python", "order_log_filter_config.py", "order_logs", shop],
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL
#         )
#     background_tasks.add_task(run_log_filter)
#     return JSONResponse(content={"message": "ログ抽出処理をバックグラウンドで開始しました"})

@log_router.get(
    "/order_log_html/combined",
    response_class=HTMLResponse,
    summary="結合注文ログ一覧表示：店舗ユーザー",
    description="`order_logs` ディレクトリ内の `combined_` から始まる結合ログファイルを HTML リストで表示します。"
)
async def list_combined_order_logs():
    if not os.path.exists(ORDER_LOG_DIR):
        raise HTTPException(status_code=404, detail="注文ログディレクトリが存在しません")

    log_files = sorted(
        [f for f in os.listdir(ORDER_LOG_DIR) if f.startswith("combined_")],
        reverse=True
    )

    if not log_files:
        return HTMLResponse("<h1>表示可能な結合ログがありません</h1>", status_code=200)

    links = [f"<li><a href='/api/v1/order_log_html/{file}'>{file}</a></li>" for file in log_files]
    return HTMLResponse(content=f"<h1>結合注文ログ一覧</h1><ul>{''.join(links)}</ul>")

# @log_router.get("/order_log_html", response_class=HTMLResponse)
# async def list_combined_order_logs():
#     log_dir = "order_logs"
#     if not os.path.exists(log_dir):
#         return "<h1>注文ログディレクトリが存在しません</h1>"
#     log_files = sorted([f for f in os.listdir(log_dir) if f.startswith("combined_")], reverse=True)
#     if not log_files:
#         return "<h1>表示可能な注文ログがありません</h1>"
#     links = [f"<li><a href='/api/v1/order_log_html/{file}'>{file}</a></li>" for file in log_files]
#     return f"<h1>結合注文ログ一覧</h1><ul>{''.join(links)}</ul>"

@log_router.get(
    "/order_log_html/combined/{filename}",
    response_class=HTMLResponse,
    summary="結合注文ログファイル表示：店舗ユーザー",
    description="指定された結合ログファイルの内容を HTML として表示します。"
)
async def view_combined_order_log(filename: str):
    log_path = os.path.join(ORDER_LOG_DIR, filename)

    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="ログファイルが存在しません")

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read().replace("\n", "<br>")
        return HTMLResponse(content=f"<h1>{filename}</h1><pre>{content}</pre>")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイルの読み込み中にエラーが発生しました: {str(e)}")

# @log_router.get("/order_log_html/{filename}", response_class=HTMLResponse)
# async def view_combined_order_log(filename: str):
#     log_path = os.path.join("order_logs", filename)
#     if not os.path.exists(log_path):
#         return HTMLResponse("ログファイルが存在しません", status_code=404)
#     with open(log_path, "r", encoding="utf-8") as f:
#         content = f.read().replace("\n", "<br>")
#     return f"<h1>{filename}</h1><pre>{content}</pre>"

