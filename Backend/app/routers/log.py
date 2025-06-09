from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from urllib.parse import quote
import os
import subprocess

log_router = APIRouter(prefix="/api/v1", tags=["log"])

LOG_DIR = "./logs"
ORDER_LOG_DIR = "./order_logs"


# 管理者ユーザー用：ログ一覧
@log_router.get(
    "/log_html",
    summary="一般ログ一覧取得",
    description="一般ログの一覧を取得します。",
    response_class=HTMLResponse,
    tags=["log: admin"]
)
def list_logs():
    if not os.path.exists(LOG_DIR):
        raise HTTPException(status_code=404, detail="ログディレクトリが存在しません")
    
    log_files = sorted(os.listdir(LOG_DIR), reverse=True)
    links = [f"<li><a href='/api/v1/log_html/{quote(file)}'>{file}</a></li>" for file in log_files]
    html = f"<h1>ログ一覧</h1><ul>{''.join(links)}</ul>"
    return HTMLResponse(content=html)


# 管理者ユーザー用：ログファイル内容
@log_router.get(
    "/log_html/{filename}",
    summary="一般ログ内容取得",
    description="ファイル名を指定した一般ログの内容を取得します。",
    response_class=HTMLResponse,
    tags=["log: admin"]
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


# 店舗ユーザー用：結合ログ一覧（静的ルートを先に！）
@log_router.get(
    "/order_log_html/combined",
    summary="結合注文ログ一覧取得",
    description="結合された注文ログの一覧を取得します。",
    response_class=HTMLResponse,
    tags=["log: shop"]    
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

    links = [f"<li><a href='/api/v1/order_log_html/{quote(file)}'>{file}</a></li>" for file in log_files]
    return HTMLResponse(content=f"<h1>結合注文ログ一覧</h1><ul>{''.join(links)}</ul>")


# 店舗ユーザー用：結合ログファイル表示
@log_router.get(
    "/order_log_html/combined/{filename}",
    response_class=HTMLResponse,
    summary="結合注文ログ内容取得",
    description="結合された注文ログファイルの内容を取得します。",
    tags=["log: shop"]
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


# 管理者ユーザー用：注文ログファイル一覧
@log_router.get(
    "/order_log_html",
    response_class=HTMLResponse,
    summary="注文ログ一覧取得",
    description="注文ログの一覧を取得します。",
    tags=["log: admin"]
)
def list_order_logs():
    if not os.path.exists(ORDER_LOG_DIR):
        raise HTTPException(status_code=404, detail="注文ログディレクトリが存在しません")

    files = sorted(os.listdir(ORDER_LOG_DIR), reverse=True)
    links = [f"<li><a href='/api/v1/order_log_html/{quote(f)}'>{f}</a></li>" for f in files]
    html = f"<h1>注文ログ一覧</h1><ul>{''.join(links)}</ul>"
    return HTMLResponse(content=html)


# 管理者ユーザー用：注文ログファイル内容表示（汎用）
@log_router.get(
    "/order_log_html/{filename}",
    summary="注文ログ内容取得",
    description="指定された注文ログファイルの内容を取得します。",
    response_class=HTMLResponse,
    tags=["log: admin"]
)
def view_order_log(filename: str):
    path = os.path.join(ORDER_LOG_DIR, filename)
    print(f"🔍 試行ファイル名: {filename}")
    print(f"📂 絶対パス: {os.path.abspath(path)}")
    print(f"📂 存在する?: {os.path.exists(path)}")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="注文ログファイルが存在しません")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().replace("\n", "<br>")
        return HTMLResponse(content=f"<h1>{filename}</h1><pre>{content}</pre>")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイルの読み込み中にエラーが発生しました: {str(e)}")


# 店舗ユーザー用：注文ログ抽出（バックグラウンド実行）
@log_router.get(
    "/filter_order_logs",
    summary="注文ログの抽出処理（店舗名）",
    description="指定した店舗名の注文ログを抽出する処理をバックグラウンドで実行します。",
    tags=["log: shop"]
)
async def filter_order_logs(
    background_tasks: BackgroundTasks,
    shop: str = Query(..., description="対象店舗名")
):
    def run_log_filter():
        subprocess.run(
            ["python", "order_log_filter_config.py", "order_logs", shop],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    background_tasks.add_task(run_log_filter)
    return {"message": "ログ抽出処理をバックグラウンドで開始しました"}
