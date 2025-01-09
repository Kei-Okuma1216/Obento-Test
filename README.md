# Obento-Test
お弁当注文システムの簡単なプロトタイプをここにホストします。

## venv簡易実行マニュアル
まず OpenSSLで秘密鍵→CSR→自己署名証明書の順につくっておく。
1. main.pyのあるディレクトリでcmdを押してエンターを押す（コマンドプロンプトが表れる）
2. activateする
> .\env\Scripts\activate
3. uvicornを使ってHTTPSサーバーを起動する
以下は生成した証明書と秘密鍵を使用して、uvicornでHTTPSサーバーを起動します
> uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt
4. ブラウザでアクセスする
> https://localhost:8000
5. もしエラーになれば、詳細設定ボタン押下後、Localhostにすすむ（安全ではありません）のリンクをクリックする。 
- [ ] 未完了のタスク
- [x] 完了したタスク

## OpenSSLの設定
- OpenSSLのインストール
```winget search openssl```
```winget install ShiningLight.OpenSSL.Light```
```openssl version```
```winget list```
- OpenSSLの場所表示する
```dir /a /s c:\openssl.exe```
