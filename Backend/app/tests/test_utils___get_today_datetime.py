# test/test_utils___get_today_datetime.py
#
# 実行方法：
# pytest -s test_utils___get_today_datetime.py

import pytest
from datetime import datetime, timedelta
import pytz
import sys

from utils.utils import get_today_datetime


# このテストは、get_today_datetime() が datetime オブジェクトを返し、
# かつ tzinfo を持たない「ナイーブ」な datetime であることを確認する。
def test_get_today_datetime_returns_naive_datetime():
    result = get_today_datetime()
    sys.stdout.write(f"\nresult (naive datetime): {result}\n")
    assert isinstance(result, datetime)
    assert result.tzinfo is None


# このテストは、get_today_datetime(0) が JST（Asia/Tokyo）の「今日の0時0分0秒」を
# 正しく返していることを確認する。
def test_get_today_datetime_is_today_zero_clock():
    result = get_today_datetime()
    expected = datetime.now(pytz.timezone("Asia/Tokyo")).replace(hour=0, minute=0, second=0, microsecond=0)
    expected = datetime.strptime(expected.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    sys.stdout.write(f"result:   {result}\n")
    sys.stdout.write(f"expected: {expected}\n")
    assert result == expected


# このテストは、days_ago に 0, 1, 3, 7, 30 を与えたときに、
# JSTでそれぞれの日付の「0時0分0秒」のナイーブな datetime が返ってくるかを確認する。
@pytest.mark.parametrize("days_ago", [0, 1, 3, 7, 30])
def test_get_today_datetime_days_ago(days_ago):
    result = get_today_datetime(days_ago)
    jst = pytz.timezone("Asia/Tokyo")
    expected_date = datetime.now(jst) - timedelta(days=days_ago)
    expected = datetime(expected_date.year, expected_date.month, expected_date.day, 0, 0, 0)
    expected = datetime.strptime(expected.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    sys.stdout.write(f"[days_ago={days_ago}] result:   {result}\n")
    sys.stdout.write(f"[days_ago={days_ago}] expected: {expected}\n")
    assert result == expected
    assert result.tzinfo is None
