# app/log_unified.py
import logging
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger("uvicorn")


# def get_today_datetime(days_ago: int = 0) -> datetime:
#     """
#     JSTで days_ago 日前の0時0分0秒のナイーブな datetime を返す。
#     """
#     if not isinstance(days_ago, int) or days_ago < 0:
#         logger.warning(f"get_today_datetime() - 無効な days_ago: {days_ago}")
#         raise ValueError("days_ago は 0 以上の整数で指定してください")

#     try:
#         tz = pytz.timezone("Asia/Tokyo")
#         current_time = datetime.now(tz) - timedelta(days=days_ago)
#         naive_datetime = datetime(
#             current_time.year,
#             current_time.month,
#             current_time.day,
#             0, 0, 0
#         )
#     except Exception as e:
#         logger.exception("get_today_datetime() - 予期せぬエラーが発生しました")
#         raise RuntimeError("日付計算中に予期せぬエラーが発生しました") from e
#     else:
#         logger.debug(f"get_today_datetime() - 生成日時: {naive_datetime}")
#         return naive_datetime



class FixedWidthFormatter(logging.Formatter):
    def format(self, record):
        # levelname を左寄せで5文字幅に揃える
        record.levelname = f"{record.levelname:<5}"
        return super().format(record)

import os
from logging.handlers import TimedRotatingFileHandler  # 必要なインポート
from utils.utils import get_today_date

# 方法　２つのロガーをつくる
# from log_unified import uvicorn_logger, order_logger
# 使用例
# 通常ログ入力(引数1つ)
# logger.info("アプリケーション起動")
# 注文ログ入力(引数2つ)
# log_order("ORDER", "注文が完了しました")
def create_logger(name: str, log_dir: str) -> logging.Logger:
    """
    汎用ロガー生成関数。
    :param name: ロガー名（例: "uvicorn", "order_logger"）
    :param log_dir: 出力先ディレクトリ名
    :return: ロガーオブジェクト
    """
    # print(f"作成ログ: {name}")
    os.makedirs(log_dir, exist_ok=True)
    current_date = get_today_date()
    # print(f"current_date_with_zero: {current_date_with_zero}")
    # log_filename = os.path.join(log_dir, f"{current_time_with_zero.strftime('%Y-%m-%d')}.log")
    log_filename = os.path.join(log_dir, f"{current_date}.log")
    
    # print(f"ログファイル名: {log_filename}")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    formatter = FixedWidthFormatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = TimedRotatingFileHandler(
        log_filename, when="midnight", interval=1, encoding="utf-8", backupCount=7
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# 例: uvicorn用ロガー
# uvicorn_logger = create_logger("uvicorn", "logs")
logger = create_logger("uvicorn", "logs")
order_logger = create_logger("order_logger", "order_logs")# 例: 注文用ロガー

# 注文ログ出力インターフェース
# log_order(
#     "ORDER",
#     f"注文完了 - order_id:{order_id:>4} - company_id:{company_id}, username:{username}, shop_name:{shop_name}, menu_id:{menu_id}, amount:{amount}"
# )
def log_order(log_type: str, message: str):
    """
    注文用ログ出力インターフェース。
    :param log_type: "ORDER", "CANCEL" など
    :param message: メッセージ本文
    """
    log_message = f"{log_type.upper()}: {message}"
    order_logger.info(log_message)
    print(log_message)  # コンソールにも出力






