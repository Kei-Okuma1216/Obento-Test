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
#logger.setLevel(logging.INFO)

def set_logger_levels(logger, levels):
    """
    指定した複数のログレベルを有効にする
    :param logger: ロガーオブジェクト
    :param levels: 設定したいログレベルのリスト (例: ["INFO", "WARNING"])
    """
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    min_level = min(level_mapping[level] for level in levels if level in level_mapping)
    logger.setLevel(min_level)

# デフォルトではINFOとWARNINGを設定
#set_logger_levels(logger, ["INFO", "WARNING"])
set_logger_levels(logger, ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

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
'''ログ
1. ログレベル
ログレベルは以下の5つがあります。
DEBUG：デバッグ情報
INFO：情報
WARNING：警告
ERROR：エラー
CRITICAL：重大なエラー
2. ログ出力
logger.debug("デバッグ情報")
logger.info("情報")
logger.warning("警告")
logger.error("エラー")
logger.critical("重大なエラー")
3. フォーマット
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.WARNING)
logger.setLevel(logging.ERROR)
logger.setLevel(logging.CRITICAL)
4. ログファイル
ログファイルは1日ごとに新しいファイルを作成します。
handler = TimedRotatingFileHandler(
    log_filename, when="midnight", interval=1, encoding="utf-8", backupCount=7
)
handler.suffix = "%Y-%m-%d"  # ログファイルの名前に日付をつける
5. フォーマット設定
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
6. ログ出力
logger.debug("デバッグ情報")
logger.info("情報")
logger.warning("警告")
logger.error("エラー")
logger.critical("重大なエラー")
7. ログ出力の例
INFO:
書式：    logger.info("set_all_cookies() - cookies['sub']が存在しません")
書式：    logger.info(f"- {""} - {"root()"}, {"ルートにアクセスしました"}")
出力：    2025-03-07 10:20:51 - INFO - ルートエンドポイントにアクセスされました
ERROR:
書式：    logger.error(f"エラーが発生！- {status_code} - {method_name}, {message}")
出力：    ERROR: 2021-08-01 00:00:00,000 - ERROR - エラーが発生！- 400 - login_get(), エラーメッセージ
DEBUG:
書式：    
出力：    
'''