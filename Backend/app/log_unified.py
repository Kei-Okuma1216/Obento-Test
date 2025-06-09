# log_unified.py
'''
    1. class FixedWidthFormatter(logging.Formatter):
    2. def create_logger(name: str, log_dir: str) -> logging.Logger:
    3. logger = create_logger("app_logger", "logs")
    4. order_logger = create_logger("order_logger", "order_logs")
    5. def log_order(log_type: str, message: str):
'''
import logging

# カスタムフォーマッタ（LEVEL列を整形）
class FixedWidthFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = f"{record.levelname:<5}"
        return super().format(record)

import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# 共通のロガー作成関数
def create_logger(name: str, log_dir: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    
    current_date = current_date = datetime.now().strftime("%Y-%m-%d") #get_today_date()
    log_file = os.path.join(log_dir, f"{current_date}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # 他のloggerに伝播しない

    formatter = FixedWidthFormatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

    if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
        file_handler = TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, encoding="utf-8", backupCount=7
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# === ロガーの定義 ===
logger = create_logger("app_logger", "logs")  # 通常ログ
order_logger = create_logger("order_logger", "order_logs")  # 注文ログ

# 注文ログ専用関数
def log_order(log_type: str, message: str):
    # "CANCEL" に合わせて6文字右詰めにし、足りなければスペースで埋める
    aligned_type = log_type.upper().ljust(6)
    formatted = f"{aligned_type}: {message}"
    order_logger.info(formatted)
    print(formatted)
