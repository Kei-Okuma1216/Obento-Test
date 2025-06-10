# utils/utils.py
'''
    # utils/decorator.py
    1. log_decorator(func):
    2. deprecated(func):

    # utils/date_utils.py
    3. get_naive_jst_now() -> datetime:
    4. get_today_datetime(offset: int = 0) -> datetime:
    5. get_today_date(offset: int = 0) -> date:
    6. get_datetime_range(days_ago: int) -> Tuple[datetime, datetime]:

    # utils.cookie_helper.py
    7. set_all_cookies(response: Response, user: Dict):
    8. get_all_cookies(request: Request) -> Optional[Dict[str, str]]:
    9. delete_all_cookies(response: Response):
    10. compare_expire_date(expires: str) -> bool:
    11. set_last_order(response: Response, last_order_date: datetime):
    14. get_token_expires(request: Request) -> str:

    -12. check_order_duplex(request: Request):
    -13. get_end_of_today(tz : timezone = None) -> datetime:
    
    # utils/permission_helper.py
    15. check_permission_and_stop_order(request: Request, response: Response):
    16. check_permission(request: Request, permits: list):

    # utils/utils.py
    17. check_holiday(date: str):
    18. delivery_date_view(date_str: str):
    -19. get_username_from_userid()
'''
    
from datetime import datetime, timezone, timedelta, date

from venv import logger

from fastapi import Request, Response
from http.cookies import SimpleCookie


from models.order import select_orders_by_user_at_date
from core.constants import ERROR_FORBIDDEN_SECOND_ORDER
from database.local_postgresql_database import endpoint
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")
from models.user import select_user


