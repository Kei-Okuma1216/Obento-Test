# 管理者の権限チェック
from typing import Optional
from fastapi import Header, Request, Response
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
from utils import log_decorator

from fastapi import APIRouter
view_router = APIRouter()

# 注文一覧テーブル表示
@log_decorator
async def order_table_view(request: Request, response: Response, orders, redirect_url: str, hx_request: Optional[str] = Header(None)):
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
