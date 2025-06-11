# Pythonベースイメージを使用（スリムでOK）
FROM python:3.11-slim

# 作業ディレクトリを Backend に設定
WORKDIR /code

# git を含む依存インストール
RUN apt-get update && apt-get install -y git && \
    pip install --no-cache-dir --upgrade pip

# requirements.txt のコピーと依存インストール
COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをすべてコピー
COPY ./app ./app

# 証明書ファイルをコピー（※ compose の volumes を使う場合は不要）
# COPY ./app/core/my-local.key ./app/core/my-local.key
# COPY ./app/core/my-local.crt ./app/core/my-local.crt

# 起動は docker-compose 側で定義（command:）
