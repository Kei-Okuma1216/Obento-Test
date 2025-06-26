# routers/user.py
# ../users/me
'''
    1. regist_complete(request: Request, response: Response): 
    2. get_user_context(request: Request, orders, user_id: int):
    3. show_order_cancel_form(request: Request, user_id: int):
    4. submit_order_cancel_form(request: Request, user_id: int, order_ids: str = Form(...)):
    5. cancel_complete(request: Request, response: Response, user_id: str):
    6. view_my_order_history(request: Request, user_id: int, db: AsyncSession = Depends(get_db)):
    7. redirect_to_order_history(request: Request):
'''
from fastapi import Request, Response, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.decorator import log_decorator
from utils.helper import redirect_error
from utils.cookie_helper import get_all_cookies, set_last_order
from utils.permission_helper import check_permission


from models.user import select_user
from models.order import select_orders_by_user_ago, insert_order
from schemas.user_schemas import UserResponse
from services.order_view import order_table_view

from database.local_postgresql_database import endpoint
from log_unified import logger, log_order

templates = Jinja2Templates(directory="templates")

user_router = APIRouter()



# お弁当の注文完了　ユーザーのみ
# @log_decorator
@user_router.get(
    "/{user_id}/order_complete/",
    summary="お弁当の注文完了画面：一般ユーザー",
    description="一般ユーザーがお弁当を注文完了直後の画面",
    response_class=HTMLResponse,
    tags=["user"])
@log_decorator
async def regist_complete(request: Request, response: Response, user_id: str):

    try:
        if not await check_permission(request, [1]): # ユーザーの権限
            return templates.TemplateResponse(
                "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)

        user: UserResponse = await select_user(cookies['sub'])
        if user is None:
            logger.error("ユーザーが見つかりません: sub=%s", cookies['sub'])
            return await redirect_error(request, "ユーザー情報の取得に失敗しました", None)

        await insert_order(
            user.company_id,
            user.username,
            user.shop_name,
            user.menu_id,
            amount=1
        )

        username = user.get_username()
        orders = await select_orders_by_user_ago(username, 7)

        if not orders:
            logger.error("注文が見つかりません: username=%s", username)
            return await redirect_error(request, "注文が見つかりません", None)

        order_count = len(orders) - 1
        last_order_date = orders[order_count].created_at

        set_last_order(response, last_order_date)  # ここで注文の重複を防止

        user_context = await get_user_context(request, orders, int(user.get_id()))

        return await order_table_view(request, response, orders, "order_complete.html", user_context)

    except Exception as e:
        logger.exception("予期せぬエラーが発生しました: %s", str(e))
        return await redirect_error(request, "注文確定中に予期せぬエラーが発生しました", e)


@log_decorator
async def get_user_context(request: Request, orders, user_id: int):
    user_context = {
        'request': request,
        'base_url': endpoint,
    }
    order_context = {
        'orders': orders,
        'order_count': len(orders),
        "order_details": orders[-1].model_dump() if orders else None,
        "user_id": user_id
    }
    user_context.update(order_context)
    
    return user_context



# 注文キャンセル
# GET
# https://192.168.3.14:8000/user/1/order_cancel_form
@user_router.get(
    "/{user_id}/order_cancel_form",
    response_class=HTMLResponse,
    summary="注文キャンセルフォーム画面",
    tags=["user: cancel"])
@log_decorator
async def show_order_cancel_form(request: Request, user_id: int):
    try:
        logger.debug(f"show_order_cancel_form() - ユーザーID: {user_id}")
        return templates.TemplateResponse("order_cancel_form.html", {
            "request": request,
            "user_id": user_id
        })

    except Exception as e:
        logger.exception(f"show_order_cancel_form() - エラー発生: {e}")
        raise HTTPException(status_code=500, detail="注文キャンセルフォームの表示に失敗しました")


# POST
from fastapi import HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from database.local_postgresql_database import get_db
from schemas.order_schemas import CancelOrderRequest
from routers.order import set_order_cancel_by_user


@user_router.post(
    "/{user_id}/order_cancel_submit",
    response_class=HTMLResponse,
    summary="フォーム送信で注文キャンセル処理",
    tags=["user: cancel"])
@log_decorator
async def submit_order_cancel_form(
    request: Request,
    user_id: int,
    order_ids: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    try:
        # 入力はカンマ区切り: "101,102"
        order_id_list = [int(i.strip()) for i in order_ids.split(",") if i.strip().isdigit()]
        payload = CancelOrderRequest(order_ids=order_id_list, user_id=user_id)
        response = await set_order_cancel_by_user(payload=payload, session=session)


    except Exception as e:
        logger.exception(f"submit_order_cancel_form() - エラー発生: {e}")
        raise HTTPException(status_code=500, detail="注文キャンセルに失敗しました")
    else:
        log_order(
            "ORDER",
            f"全ての注文を削除しました。"
        )
        logger.debug(f"submit_order_cancel_form() - ユーザーID: {user_id}")
        return templates.TemplateResponse("order_cancel.html", {
            "request": request,
            "user_id": user_id,
            "canceled_order_ids": response.get("canceled_order_ids", [])
        })

# テスト方法
# curl -X POST "https://192.168.3.14:8000/user/2/order/cancel" \
#   -H "Content-Type: application/json" \
#   -d '{"order_ids": [14]}'




''' 開発中止する ユーザーのメニュー選択 '''
'''@user_router.post("/me", response_class=HTMLResponse, tags=["user"])
@user_router.get("/me", response_class=HTMLResponse, tags=["user"])
@log_decorator
async def get_user_shop_menu(request: Request, response: Response):
    # ユーザーお弁当屋のメニュー選択
    try:
        permits = [1, 2, 10, 99] # ユーザーの権限
        if await check_permission(request, permits) == False:
            return templates.TemplateResponse(
            "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)
        if not cookies:
            raise CookieException(method_name="get_all_cookies()")

        # メニュー一覧
        menus = await select_all_menus(default_shop_name)
        #logger.debug(f"shop_name: {'shop01'}")

        if menus is None:
            logger.debug('get_user_shop_menu - menusなし')

            return HTMLResponse("<html><p>メニューは0件です</p></html>")

        logger.debug(f"menus取得 {menus}")

        return await menu_cards_view(request, response, menus, "shop_menu.html")

    except SQLException as e:
        raise
    except Exception as e:
        raise CustomException(
            status.HTTP_400_BAD_REQUEST,
            f"/get_user_shop_menu()",
            f"Error: {str(e)}")
'''
from models.order import update_order

''' 注文キャンセル完了画面 一般ユーザーのみ
    ユーザーが注文をキャンセルした後の画面'''
    # https://192.168.3.14:8000/user/1/order_cancel_complete/
@log_decorator
@user_router.get(
    "/{user_id}/order_cancel_complete/",
    summary="お弁当の注文キャンセル完了画面：一般ユーザー",
    description="一般ユーザーがお弁当を注文キャンセル完了直後の画面",
    response_class=HTMLResponse,
    tags=["user: cancel"])
async def cancel_complete(request: Request, response: Response, user_id: str):

    try:
        if not await check_permission(request, [1]): # ユーザーの権限
            return templates.TemplateResponse(
                "Unauthorized.html", {"request": request})

        cookies = get_all_cookies(request)

        user: UserResponse = await select_user(cookies['sub'])
        if user is None:
            logger.error("ユーザーが見つかりません: sub=%s", cookies['sub'])
            return await redirect_error(request, "ユーザー情報の取得に失敗しました", None)

        username = user.get_username()
        orders = await select_orders_by_user_ago(username, 0)

        if not orders:
            logger.error("注文が見つかりません: username=%s", username)
            return await redirect_error(request, "注文が見つかりません", None)

        # 最新の注文を取得
        orders.sort(key=lambda x: x.created_at, reverse=True)
        order_id = orders[0].order_id
        
        # 最新の注文をキャンセルする
        if await update_order(order_id, "canceled", "True")== False:
            logger.error("注文の更新に失敗しました: order_id=%s", order_id)
            return await redirect_error(request, "注文の更新に失敗しました", None)

    except Exception as e:
        logger.exception("予期せぬエラーが発生しました: %s", str(e))
        return await redirect_error(request, "注文確定中に予期せぬエラーが発生しました", e)
    else:
        logger.info("注文の更新に成功しました: order_id=%s", order_id)
        log_order(
            "CANCEL", f"注文取消 - order_id: {order_id} - username: {username}"
        )
        # ✅ 最終的にキャンセル完了画面を表示
        return templates.TemplateResponse("order_cancel.html", {
            "request": request,
            "user_id": user.user_id,
            "canceled_order_id": order_id
        })


from database.local_postgresql_database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models.order import select_orders_by_user_all
from models.user import select_user
from core.security import decode_jwt_token
from utils.helper import redirect_login_failure

from fastapi import Response


@user_router.get(
    "/{user_id}/order/history",
    summary="注文履歴表示のエントリポイント",
    description="一般ユーザーが注文履歴を表示する。NFCタグを読んでこのURLにアクセスする。その後Cookieの値により一般ユーザーの場合、自身の注文履歴を表示する。",
    response_class=HTMLResponse,
    tags=["user : order history"])
@log_decorator
async def view_my_order_history(
    request: Request, user_id: int, db: AsyncSession = Depends(get_db)):
    # https://localhost:8000/user/1/order/history
    try:
        logger.debug("=== view_my_order_history 開始 ===")
        token = request.cookies.get("token")
        if not token:
            return redirect_login_failure(request, "ログインが必要です")
        logger.debug("token 取得成功")
        payload = decode_jwt_token(token)
        username = payload["sub"]
        logger.debug("username 取得成功")

        user = await select_user(username)
        if user is None:
            return redirect_login_failure(request, "ユーザー情報が取得できません")

        orders = await select_orders_by_user_all(username)
        if not orders:
            logger.info("注文履歴がありません")
            return templates.TemplateResponse("no_orders.html", {
                "request": request,
                "message": "注文履歴がありません",
                "user_id": user.get_id()
            })
        logger.debug(f"ordersの件数は {len(orders)} ")

    except Exception:
        logger.exception("注文履歴の取得に失敗しました")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "注文履歴の取得中にエラーが発生しました",
            "status_code": 500
        })
    else:
        from routers.user import get_user_context
        user_context = await get_user_context(request, orders, user.get_id())
        user_context['name'] = user.get_name()
        
        logger.info(f"user_contextの取得に成功しました{user_context=}")

        from services.order_view import order_table_view
        from fastapi.responses import Response
        response = Response()

        logger.info("注文履歴の取得に成功しました")
        return await order_table_view(request, response, orders, "order_history.html", user_context)


from fastapi.responses import RedirectResponse
# https://localhost:8000/user/history
@user_router.get(
    "/history",
    summary="簡易注文履歴アクセス",
    description="ユーザー名（Cookie）からuser_idを逆引きして、正式な注文履歴ページにリダイレクトする。",
    tags=["user : redirect"]
)
@log_decorator
async def redirect_to_order_history(request: Request):
    try:
        token = request.cookies.get("token")
        if not token:
            return redirect_login_failure(request, "ログインが必要です")

        payload = decode_jwt_token(token)
        username = payload["sub"]
        logger.debug(f"username取得成功: {username}")

        user = await select_user(username)
        if user is None:
            return redirect_login_failure(request, "ユーザー情報が取得できません")

        user_id = user.get_id()
        redirect_url = f"/user/{user_id}/order/history"
        logger.info(f"/hogehoge → {redirect_url} にリダイレクトします")
        return RedirectResponse(url=redirect_url, status_code=303)

    except Exception:
        logger.exception("hogehogeリダイレクトに失敗しました")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "自動リダイレクトに失敗しました",
            "status_code": 500
        })


# print("✅ user_router モジュールが読み込まれました")
