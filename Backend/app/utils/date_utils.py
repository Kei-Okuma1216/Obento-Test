# utils/date_utils.py
'''
    日付・時刻の取得を行うヘルパー関数群
    1. get_naive_jst_now() -> datetime:
    2. get_today_datetime(offset: int = 0) -> datetime:
    3. get_today_date(offset: int = 0) -> date:
    4. class Period(NamedTuple):
    5. get_datetime_range(days_ago: int) -> Tuple[datetime, datetime]:
'''
from fastapi import HTTPException, status
from datetime import datetime, date, timedelta
import pytz

from utils.utils import log_decorator
# from log_unified import logger


# @log_decorator
def get_naive_jst_now() -> datetime:
    """Asia/Tokyo の現在時刻を tzinfo なしで返す
    日付取得はasyncにする必要なし
    """
    time_now = datetime.strptime(
        datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S"),
        "%Y-%m-%d %H:%M:%S"
    )
    # logger.debug(f"get_naive_jst_now() - 現在のナイーブなJST時刻: {time_now}")
    return time_now


# @log_decorator



# @log_decorator
def get_today_datetime(offset: int = 0) -> date:
    """
    JSTで offset 日前の0時0分0秒のナイーブな datetime を返す。
    例: offset=0 -> 今日の 00:00:00（タイムゾーンなし）
    """
    try:
        # 型と値の検証
        if not isinstance(offset, int):
            # logger.warning(f"get_today_datetime() - 無効な offset: {offset}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="offset は 整数で指定してください"
            )

        tz = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(tz) + timedelta(days=offset)

        naive_datetime = datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            0, 0, 0
        )

    except HTTPException:
        raise  # 既に投げた HTTPException はそのまま返す
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日付計算中に不正なパラメータが指定されました"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="日付計算中にサーバーエラーが発生しました"
        )
    else:
        # from log_unified import logger
        # logger.debug(f"get_today_datetime(): {naive_datetime}")
        return naive_datetime


# 今日の日付取得 update_datetime用
from datetime import timedelta, date
from fastapi import HTTPException, status

@log_decorator
def get_today_date(offset: int = 0) -> date:
    """
    今日の日付 (date型) を取得する関数。
    オプションで日数オフセットを指定可能。

    :param offset: 今日からのオフセット日数 (例: 昨日は -1, 明日は +1)
    :return: date型の日付 (時刻なし)

    d = get_today_date()
    print(d)  # 例: 2025-05-14

    # 文字列にしたい場合
    formatted = d.strftime("%Y/%m/%d")
    print(formatted)  # 例: 2025/05/14    
    """
    try:
        if not isinstance(offset, int):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="offset は整数で指定してください"
            )

        from utils.utils import get_today_datetime  # 循環インポート注意
        new_datetime = get_today_datetime() + timedelta(days=offset)
        result_date = new_datetime.date()

        # from log_unified import logger
        # logger.debug(f"get_today_date(): {result_date}")  # デバッグ出力

        return result_date

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"日付取得処理中にエラーが発生しました: {str(e)}"
        )


from typing import NamedTuple

class Period(NamedTuple):
    # 返却値が入れ替わるので、専用のクラスを作った
    start: datetime
    end: datetime

# @log_decorator
async def get_datetime_range(days_ago: int) -> Period:
    """
    指定された days_ago に基づいて、期間の開始日時と終了日時を返す。
    返す datetime は tzinfo を持たない naive datetime。
    開始: 00:00:00、終了: 23:59:59
    """
    try:
        # 型と値の検証
        if not isinstance(days_ago, int) or days_ago < 0:
            # logger.warning(f"get_datetime_range() - 無効な days_ago: {days_ago}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_ago は 0 以上の整数で指定してください"
            )

        # now = datetime.now(pytz.timezone("Asia/Tokyo"))
        now = get_naive_jst_now()
        start_target = now - timedelta(days=days_ago)
        end_target = now
        # # 00:00:00 と 23:59:59.999999 の datetime を作成
        # start_dt = f"{target_date.isoformat()} 00:00:00"
        # end_dt = f"{target_date.isoformat()} 23:59:59"
        # start_dt = datetime.combine(target_date, time.min)
        # end_dt = datetime.combine(target_date, time.max)
        start_dt = datetime(start_target.year, start_target.month, start_target.day, 0, 0, 0)
        end_dt   = datetime(end_target.year, end_target.month, end_target.day, 23, 59, 59)

    except HTTPException:
        raise  # 既に投げた HTTPException はそのまま再スロー
    except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="期間計算中に不正なパラメータが指定されました"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="期間計算中にサーバーエラーが発生しました"
        )
    else:
        return Period(start_dt, end_dt)

