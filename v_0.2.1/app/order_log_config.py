# order_log_config.py
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from utils.utils import get_today_datetime

# 注文ログ用のディレクトリを作成（※ディレクトリ名はadmin側と統一する必要があります）
log_dir = "order_logs"
os.makedirs(log_dir, exist_ok=True)

# 日付付きのログファイル名を生成
current_time = get_today_datetime() # get_now(JST)
log_filename = os.path.join(log_dir, f"{current_time.strftime('%Y-%m-%d')}.log")

# 注文ログ専用のロガーを作成
_order_logger = logging.getLogger("order_logger")
_order_logger.propagate = False
_order_logger.setLevel(logging.DEBUG)

# ファイルハンドラー（1日ごとに新しいログファイルを作成）
file_handler = TimedRotatingFileHandler(
    log_filename, when="midnight", interval=1, encoding="utf-8", backupCount=7
)
file_handler.suffix = "%Y-%m-%d"

# コンソールハンドラー（オプション）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# フォーマット設定
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# ロガーにハンドラーを追加
_order_logger.addHandler(file_handler)
#_order_logger.addHandler(console_handler)

def order_logger(log_type: str, message: str):
    """
    注文に関するログを記録する関数。
    log_type: "ORDER" や "CANCEL" など、注文完了やキャンセルを示すタイプ
    message: ログに記録するメッセージ
    """
    # ログメッセージの先頭にタイプを付与
    log_message = f"{log_type.upper()}: {message}"
    # INFOレベルで記録（必要に応じてレベルを変更可能）
    _order_logger.info(log_message)

# ログのテスト
#order_logger("ORDER", "注文が完了しました")
#order_logger("CANCEL", "注文がキャンセルされました")

# insert_order()を参照されたし
#order_logger("ORDER", f"注文完了 - order_id:{order_id} - shop_name:{shop_name}:{menu_id} - {company_id}:{username},{amount}")

