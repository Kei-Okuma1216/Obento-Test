# app/log_unified.py
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from utils.utils import get_today_datetime

def create_logger(name: str, log_dir: str) -> logging.Logger:
    """
    汎用ロガー生成関数。
    :param name: ロガー名（例: "uvicorn", "order_logger"）
    :param log_dir: 出力先ディレクトリ名
    :return: ロガーオブジェクト
    """
    print(f"create_logger: {name}")
    os.makedirs(log_dir, exist_ok=True)
    current_time = get_today_datetime()
    print(f"current_time: {current_time}")
    log_filename = os.path.join(log_dir, f"{current_time.strftime('%Y-%m-%d')}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

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

def log_order(log_type: str, message: str):
    """
    注文用ログ出力インターフェース。
    :param log_type: "ORDER", "CANCEL" など
    :param message: メッセージ本文
    """
    log_message = f"{log_type.upper()}: {message}"
    order_logger.info(log_message)

# ログの使用例
# uvicorn_logger.info("アプリケーション起動")
# log_order("ORDER", "注文が完了しました")

# 方法１　２つのロガーをつくる
# from log_unified import uvicorn_logger, order_logger
# 方法２　１つのロガーを選択する
# logger = create_logger("default_logger", "logs")
# from log_unified import logger
