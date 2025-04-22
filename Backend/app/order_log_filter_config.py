import os
import glob
import sys

# コマンドライン引数からログフォルダを取得（指定がなければ "order_logs" を使用）
logs_dir = sys.argv[1] if len(sys.argv) > 1 else "order_logs"
# コマンドライン引数から抽出対象のショップ名を取得（指定がなければ "shop01"）
shop_name = sys.argv[2] if len(sys.argv) > 2 else "shop01"

# ログフォルダ内のすべての .log ファイルを取得し、ファイル名でソートする
log_files = sorted(glob.glob(os.path.join(logs_dir, "*.log")))

# 抽出された行を格納するリスト
combined_lines = []

# 各ログファイルを順番に読み込む
for log_file in log_files:
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if shop_name in line:
                combined_lines.append(line)

# 抽出結果を新規ファイルに書き出す（例：combined_shop01.log）
output_file_path = os.path.join(logs_dir, f"combined_{shop_name}.log")
with open(output_file_path, "w", encoding="utf-8") as out_f:
    out_f.writelines(combined_lines)

print(f"抽出結果を {output_file_path} に書き出しました。")
# 入力例:
# python order_log_filter_config.py order_logs shop01
