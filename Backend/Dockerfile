# C:\Obento-Test\Backend\Dockerfile
# ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# システム依存ツールのインストール（1 RUN にまとめるとレイヤも節約）
RUN apt-get update && \
    apt-get install -y iputils-ping curl git && \
    rm -rf /var/lib/apt/lists/*

# requirements.txt のコピーと依存インストール
COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをすべてコピー
COPY ./app .
COPY ./certs ./certs

# Pythonの検索パスに /app を追加
ENV PYTHONPATH=/app
ENV TZ=Asia/Tokyo

# 起動コマンド SSL接続の場合　# 本番用 https://localhost:8000/
## ENTRYPOINT ["uvicorn"] # 不要
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile=/app/core/my-local.key", "--ssl-certfile=/app/core/my-local.crt"]
# 開発用 http://localhost:8000/
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfileコマンド
# 1. イメージのビルド
# docker build --no-cache -t fastapi:0.1.0 .
# 2. コンテナの起動
# docker run [-d] --rm [-p 8000:8000] [--name test-fastapi] fastapi:0.1.0
# 3. アクセス確認：
# http://localhost:8000
# 4. コンテナに入り込んで調査できる
# docker run -it --entrypoint /bin/bash fastapi:0.1.0
# docker compose run --rm --entrypoint sh web

# 1. uvicorn がインストールされているか確認
# 2. pip list で依存関係チェック
# 3. python main.py のような手動起動テスト
# 4. exit

# ビルドパーサの警告のみなので、以下は無視してよい。
# 1 warning found:
# - JSONArgsRecommended: JSON arguments recommended for CMD to prevent unintended behavior related to OS signals

# 証明書ファイルをコピー（※ compose の volumes を使う場合は不要）
# COPY ./app/core/my-local.key ./app/core/my-local.key
# COPY ./app/core/my-local.crt ./app/core/my-local.crt

# 起動は docker-compose 側で定義（command:）
