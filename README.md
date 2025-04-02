# Obento-Test
お弁当注文システムの簡単なプロトタイプをここにホストします。

## venv簡易実行マニュアル
0. OpenSSLで秘密鍵→CSR→自己署名証明書の順につくる
1. 仮想環境の作成 ```python -m venv env```
2. activateする
```.\env\Scripts\activate```
3. 生成した証明書と秘密鍵を使用して、uvicornでHTTPSサーバーを起動します
```uvicorn main:app --host (PCのIPアドレス) --port 8000 --ssl-keyfile=./＊＊local.key --ssl-certfile=./＊＊local.crt```
4. ブラウザ表示
```https://localhost:8000```
```http://127.0.0.1:8000```
5. 初回アクセスでは、詳細設定ボタン押下後、Localhostにすすむ（安全ではありません）のリンクをクリックする。 

## OpenSSLの設定
- OpenSSLのインストール
- ```winget search openssl```
- ```winget install ShiningLight.OpenSSL.Light```
- ```openssl version```
- ```winget list```
- OpenSSLの場所表示する
   - ```dir /a /s c:\openssl.exe```
