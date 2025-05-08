import os
import glob
import sys
from collections import defaultdict

logs_dir = sys.argv[1] if len(sys.argv) > 1 else "order_logs"
shop_name = sys.argv[2] if len(sys.argv) > 2 else "shop01"

log_files = sorted(glob.glob(os.path.join(logs_dir, "*.log")))

# 抽出前に既存の combined_ログをすべて削除
for file in glob.glob(os.path.join(logs_dir, f"combined_{shop_name}_*.log")):
    os.remove(file)


# ファイル単位で行をまとめる辞書
lines_by_date = defaultdict(list)

for log_file in log_files:
    file_date = os.path.splitext(os.path.basename(log_file))[0]  # 例: 2025-05-08
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if shop_name in line:
                lines_by_date[file_date].append(line)

# 各日付ごとに出力
for file_date, lines in lines_by_date.items():
    output_filename = f"combined_{shop_name}_{file_date}.log"
    output_path = os.path.join(logs_dir, output_filename)

    # ★ 既存ファイルを削除して上書き防止
    if os.path.exists(output_path):
        os.remove(output_path)

    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.writelines(lines)
    print(f"→ {output_path} に書き出しました。")


# import os
# import glob
# import sys
# from collections import defaultdict

# # コマンドライン引数からログフォルダを取得（指定がなければ "order_logs" を使用）
# logs_dir = sys.argv[1] if len(sys.argv) > 1 else "order_logs"
# # コマンドライン引数から抽出対象のショップ名を取得（指定がなければ "shop01"）
# shop_name = sys.argv[2] if len(sys.argv) > 2 else "shop01"

# # ログフォルダ内のすべての .log ファイルを取得し、ファイル名でソートする
# log_files = sorted(glob.glob(os.path.join(logs_dir, "*.log")))

# # 抽出された行を格納するリスト
# combined_lines = []

# # 各ログファイルを順番に読み込む
# for log_file in log_files:
#     with open(log_file, "r", encoding="utf-8") as f:
#         for line in f:
#             if shop_name in line:
#                 combined_lines.append(line)

# # 抽出結果を新規ファイルに書き出す（例：combined_shop01.log）
# output_file_path = os.path.join(logs_dir, f"combined_{shop_name}.log")
# with open(output_file_path, "w", encoding="utf-8") as out_f:
#     out_f.writelines(combined_lines)

# print(f"抽出結果を {output_file_path} に書き出しました。")
# # 入力例:
# # python order_log_filter_config.py order_logs shop01
