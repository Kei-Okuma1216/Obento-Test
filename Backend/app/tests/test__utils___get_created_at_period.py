# test/test_utils___get_created_at_period.py
# 実行方法
# pytest -s test_utils___get_today_datetime.py

import pytest
from datetime import datetime, timedelta
import pytz
import asyncio

from utils.utils import get_created_at_period

# ----------------------------------------------------------
# 📌 補助関数
# JSTで days_ago 日前の 00:00:00（ナイーブ）を期待値として返す
# get_created_at_period() の start_dt と比較する用途
# ----------------------------------------------------------
def get_expected_start(days_ago: int) -> datetime:
    jst = pytz.timezone("Asia/Tokyo")
    target = datetime.now(jst) - timedelta(days=days_ago)
    expected = datetime(target.year, target.month, target.day, 0, 0, 0)
    return expected

# ----------------------------------------------------------
# 📌 補助関数
# 本日（JST）の 23:59:59（ナイーブ）を期待値として返す
# get_created_at_period() の end_dt と比較する用途
# ----------------------------------------------------------
def get_expected_end() -> datetime:
    jst = pytz.timezone("Asia/Tokyo")
    target = datetime.now(jst)
    expected = datetime(target.year, target.month, target.day, 23, 59, 59)
    return expected

# ----------------------------------------------------------
# 📌 テスト本体
# get_created_at_period(days_ago) が正しく以下を満たすかを検証：
# - start_dt は days_ago 日前の JST 00:00:00（ナイーブ）
# - end_dt は 本日 JST の 23:59:59（ナイーブ）
# - いずれも tzinfo を持たないナイーブな datetime
# ----------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("days_ago", [0, 1, 3, 7, 30])
async def test_get_created_at_period_returns_correct_range(days_ago):
    start_dt, end_dt = await get_created_at_period(days_ago)

    expected_start = get_expected_start(days_ago)
    expected_end = get_expected_end()

    # テスト結果出力（任意）
    print(f"[days_ago={days_ago}] start_dt:        {start_dt}")
    print(f"[days_ago={days_ago}] expected_start:   {expected_start}")
    print(f"[days_ago={days_ago}] end_dt:          {end_dt}")
    print(f"[days_ago={days_ago}] expected_end:     {expected_end}")

    # ✅ 値の正しさを検証
    assert start_dt == expected_start, "start_dt が期待通りではありません"
    assert end_dt == expected_end, "end_dt が期待通りではありません"

    # ✅ tzinfo が None（ナイーブ）であることを検証
    assert start_dt.tzinfo is None, "start_dt はナイーブな datetime であるべきです"
    assert end_dt.tzinfo is None, "end_dt はナイーブな datetime であるべきです"
