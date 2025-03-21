# user.py
# users/me
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.exception import CookieException

templates = Jinja2Templates(directory="templates")

from services import order_table_view
from database.sqlite_database import select_shop_order, select_user, insert_order
from utils import get_all_cookies, log_decorator


from fastapi import APIRouter

user_router = APIRouter()


@user_router.get("/order_complete",response_class=HTMLResponse, tags=["users"]) 
@log_decorator
async def regist_complete(request: Request, response: Response): 
    # お弁当の注文完了　ユーザーのみ
    try:
        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="regist_complete()")

        user = await select_user(cookies['sub'])

        if user is None:
            print(f"user:{user} 取得に失敗しました")
            return HTMLResponse("<html><p>user 取得に失敗しました</p></html>")

        await insert_order(
            user.company_id,
            user.username,
            user.shop_name,
            user.menu_id,
            amount=1)

        orders = await select_shop_order(
            user.shop_name, -7, user.username)

        if orders is None or len(orders) == 0:
            print("No orders found or error occurred.")
            return HTMLResponse("<html><p>注文が見つかりません。</p></html>")

        #await show_all_orders()

        main_view = "order_complete.html"
        return await order_table_view(request, response, orders, main_view)

    except CookieException as e:
        raise
    except Exception as e:
        orders = []
        print(f"/order_complete Error: {str(e)}")
        return HTMLResponse(f"<html><p>エラーが発生しました: {str(e)}</p></html>")

