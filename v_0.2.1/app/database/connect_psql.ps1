# 接続情報を指定
$DBHost = "localhost"  # データベースサーバーのホスト名
$DBPort = "5432"       # ポート番号（デフォルトは5432）
$DBName = "example"  # データベース名
$DBUser = "postgres"      # ユーザー名
$DBPassword = "root"  # パスワード

# PGPASSWORD環境変数を設定
[System.Environment]::SetEnvironmentVariable("PGPASSWORD", $DBPassword, "Process")

# psql接続コマンドを実行
Start-Process -NoNewWindow -FilePath "psql" -ArgumentList "-h $DBHost -p $DBPort -U $DBUser -d $DBName"

# PGPASSWORD環境変数を削除
[System.Environment]::SetEnvironmentVariable("PGPASSWORD", $null, "Process") 

# このコマンドを実行してください
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# ディレクトリ移動後に実行します
# .\connect_psql.ps1