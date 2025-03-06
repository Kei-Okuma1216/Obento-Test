# log_config
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from utils.utils import JST, get_now
# ログディレクトリの作成
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 日付付きのログファイル名
current_time = get_now(JST)
log_filename = os.path.join(log_dir, f"{current_time.strftime('%Y-%m-%d')}.log")

# ログ設定
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

# ハンドラー（1日ごとに新しいログファイルを作成）
handler = TimedRotatingFileHandler(
    log_filename, when="midnight", interval=1, encoding="utf-8", backupCount=7
)
handler.suffix = "%Y-%m-%d"  # ログファイルの名前に日付をつける

# フォーマット設定
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

# ロガーにハンドラーを追加
logger.addHandler(handler)
# -----------------------------------------------------