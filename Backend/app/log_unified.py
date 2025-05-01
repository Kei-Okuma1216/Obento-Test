# app/log_unified.py
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from utils.utils import get_today_datetime

class FixedWidthFormatter(logging.Formatter):
    def format(self, record):
        # levelname を左寄せで5文字幅に揃える
        record.levelname = f"{record.levelname:<5}"
        return super().format(record)
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
    print(f"作成ログ: {name}")
    os.makedirs(log_dir, exist_ok=True)
    current_time = get_today_datetime()
    # print(f"current_time: {current_time}")
    log_filename = os.path.join(log_dir, f"{current_time.strftime('%Y-%m-%d')}.log")
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
#     f"注文完了 - order_id:{order_id:>4} - {company_id}:{username}, {shop_name}:{menu_id}, {amount}"
# )
def log_order(log_type: str, message: str):
    """
    注文用ログ出力インターフェース。
    :param log_type: "ORDER", "CANCEL" など
    :param message: メッセージ本文
    """
    log_message = f"{log_type.upper()}: {message}"
    order_logger.info(log_message)






