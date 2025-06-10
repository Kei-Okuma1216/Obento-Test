# utils/utils.py
'''
    10. compare_expire_date(expires: str) -> bool:
    11. set_last_order(response: Response, last_order_date: datetime):
    12. get_last_order(request: Request):
    
    # permission_helper.pyのみ
    16. check_permission(request: Request, permits: list):


'''
from utils.decorator import log_decorator

from models.order import select_orders_by_user_at_date
from core.constants import ERROR_FORBIDDEN_SECOND_ORDER
from database.local_postgresql_database import endpoint
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")


