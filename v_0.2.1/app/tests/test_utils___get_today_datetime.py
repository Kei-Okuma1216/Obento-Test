# test/test_utils.py
#
# 実行方法：
# pytest test_utils.py

import pytest
from datetime import datetime, timedelta
import pytz

from utils.utils import get_today_datetime


def test_get_today_datetime_returns_naive_datetime():
    result = get_today_datetime()
    assert isinstance(result, datetime)
    assert result.tzinfo is None  # ナイーブであること

def test_get_today_datetime_is_today_zero_clock():
    result = get_today_datetime()
    expected = datetime.now(pytz.timezone("Asia/Tokyo")).replace(hour=0, minute=0, second=0, microsecond=0)
    expected = datetime.strptime(expected.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    assert result == expected

@pytest.mark.parametrize("days_ago", [1, 3, 7, 30])
def test_get_today_datetime_days_ago(days_ago):
    result = get_today_datetime(days_ago)
    jst = pytz.timezone("Asia/Tokyo")
    expected_date = datetime.now(jst) - timedelta(days=days_ago)
    expected = datetime(expected_date.year, expected_date.month, expected_date.day, 0, 0, 0)
    expected = datetime.strptime(expected.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")

    assert result == expected
    assert result.tzinfo is None
