# routers/log.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
import os
from datetime import date

log_router = APIRouter(prefix="/api/v1", tags=["logs"])

LOG_DIR = "./logs"
ORDER_LOG_DIR = "./order_logs"

@log_router.get("/log_html", response_class=HTMLResponse)
def list_logs():
    if not os.path.exists(LOG_DIR):
        return "<h1>ログディレクトリが存在しません</h1>"
    log_files = sorted(os.listdir(LOG_DIR), reverse=True)
    links = [f"<li><a href='/api/v1/log_html/{file}'>{file}</a></li>" for file in log_files]
    return f"<h1>ログ一覧</h1><ul>{''.join(links)}</ul>"

@log_router.get("/log_html/{filename}", response_class=HTMLResponse)
def view_log(filename: str):
    path = os.path.join(LOG_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().replace('\n', '<br>')
        return f"<h1>{filename}</h1><pre>{content}</pre>"
    else:
        return HTMLResponse("ログファイルが存在しません。", status_code=404)

@log_router.get("/order_log_html", response_class=HTMLResponse)
def list_order_logs():
    if not os.path.exists(ORDER_LOG_DIR):
        return "<h1>注文ログディレクトリが存在しません</h1>"
    files = sorted(os.listdir(ORDER_LOG_DIR), reverse=True)
    links = [f"<li><a href='/api/v1/order_log_html/{f}'>{f}</a></li>" for f in files]
    return f"<h1>注文ログ一覧</h1><ul>{''.join(links)}</ul>"

@log_router.get("/order_log_html/{filename}", response_class=HTMLResponse)
def view_order_log(filename: str):
    path = os.path.join(ORDER_LOG_DIR, filename)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().replace('\n', '<br>')
            return f"<h1>{filename}</h1><pre>{content}</pre>"
        else:
            return HTMLResponse("注文ログファイルが存在しません。", status_code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
