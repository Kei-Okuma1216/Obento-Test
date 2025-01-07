
# FastAPI実装調査


## 簡易テストコード実行方法

<details><summary>環境構築方法</summary>

### インストール
```bash
pip install fastapi uvicorn
```
</details>


<details><summary>仮想環境の作成</summary>

#### 仮想環境の作成

1. 実装調査パスを ```cmd``` で開く
```C:\Users\tensy\OneDrive\ドキュメント\okuma\お弁当注文システム\実装調査```
2. 仮想環境を作成
   ```python -m venv env```
</details>

<details><summary>アプリの配置</summary>

#### アプリの配置
3. 以下のappの含まれる```main.py```ファイルを配置する
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```
</details>

<details><summary>仮想環境での実行</summary>

#### 仮想環境での実行
4. 仮想環境をactivateする
   ```.\env\Scripts\activate```
5. コマンドプロンプトでサーバにプログラムをロードする。
   ```uvicorn main:app --reload```
6. ブラウザで URLに移動する。<br />
   ```http://127.0.0.1:8000```<br />
   ```http://127.0.0.1:8000/items/1?q=test```<br />
   ```http://127.0.0.1:8000/login/001?password=testPass```<br />
7. 終了する
    ```Ctrl + C```
8. 仮想環境を終了する
   ```deactivate```
</details>

## ログイン認証のテスト

<details><summary>概要</summary>

#### 概要
##### サーバーに毎回ログオン不要にするため、サーバーからシグネチャー(Base64Encodingの暗号化文字列)をもらい、それを使って毎回認証の代わりとする。
   1. ユーザーはNFCタグを読み込むと、初回の場合はユーザーIDを登録してサーバーから”シグネチャ”をもらう（シグネチャの中身はBase64Encode文字列）
   2. 2回目以降はそのシグネチャと注文件数でサーバーにアクセスすると注文になる。
   3. シグネチャが古くなると注文できなくなる。再度ユーザーIDで登録（期間延長）する。
   4. シグネチャーはCookieに保存する予定。
</details>

<details><summary>具体的な流れ</summary>

#### 具体的な流れ
- 登録URLと注文URLは兼用である。
- もし注文URLのみでシグネチャ無し
   - 初期登録画面もしくはユーザーログオン画面に遷移する。
- もし注文URL+シグネチャあり
   - 登録修正画面に遷移する。
- もし登録URL以外にアクセスする
   - アクセスエラーを表示する。
- 初期登録が正常に完了する
   - ユーザーにシグネチャを返す。
- ユーザーは自身のスマホに、シグネチャを保存する。

- 次回からユーザーは注文URLにユーザーのシグネチャと数量を付加してアクセスする。
- サーバーはシグネチャを検証する
   - シグネチャが正しくない
      - エラーを表示する。　
   - シグネチャが正しい
      - 正常な注文処理とする。
</details>

<details><summary>Base64Encodingのつくりかた</summary>

#### Base64Encodingのつくりかた
- ローカル環境ではOpenSSLで自己署名証明書を作る。
- これだけは必ず守るようにする！
   1. httpsを必ず使う
   2. 暗号化アルゴリズムをnone（署名なし）にしない
   3. トークンのライフサイクルをできるだけ適切にしてリフレッシュする
</details>

<details><summary>OpenSSLのインストール</summary>

#### ローカル環境にOpenSSLのインストール
1. [ガイドを読む](https://atmarkit.itmedia.co.jp/ait/articles/1601/29/news043.html)

2. [OpenSSLインストーラー x64 exe light](https://slproweb.com/products/Win32OpenSSL.html)

3. インストールの具体的な手順
[【Windows 10／11】WindowsにOpenSSL Ver.3をインストールして証明書を取り扱う）](https://atmarkit.itmedia.co.jp/ait/articles/2406/19/news033.html)

- ```winget search openssl```
- ```winget install ShiningLight.OpenSSL.Light```
- ```openssl version```
- ```winget list```
- OpenSSLの場所表示する
   - ```dir /a /s c:\openssl.exe```

4. Pathの設定
- ```Ctrl + R```
- ```SystemPropertiesAdvanced```
<!--
#### LetsEncryptの使用
##### Certbotのインストール(しかし自己署名には不要だった)
- LetsEncryptを使うが、アカウント作成は不要だが、certbotのインストールが必要。
- [Windows版Certbotのインストール手順](https://migi.me/memo/certbot-ssl-sakura/)

- certbotはwingetでインストールできた。
```winget install Certbot EFF.Certbot```<br><br>
```certbot certonly --manual -d ten-system.com -d ten-system.com -m 'k.okuma@ten-system.com' --agree-tos```<br>
```certbot --help```
<br><br>

- コマンドプロンプトで管理者で下記を実行する。<br>
```certbot certonly --manual -d ten-system.com -d ten-system.com -m 'k.okuma@ten-system.com' --agree-tos```
-->
</details>

<details><summary>OpenSSLで自己署名証明書をつくる</summary>

#### OpenSSLで自己署名証明書をつくる

- コマンドプロンプトで生成先に移動します。
- OpenSSLを使って、自己署名証明書の生成します。<br>
```openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout my-local.key -out my-local.crt -subj "/C=JP/ST=Yamaguchi/L=Shimonoseki/O=Tensystem/OU=WebApplication/CN=localhost"```
- すると```my-local.key```と```my-local.crt```ができた。

</details>

<details><summary>hostsファイルの編集</summary>

### hostsファイルの編集
***- 注意：ここは自己署名証明書の生成でCN=localhostと指定してあるので、hostsの編集は不要。***
~~- メモ帳を管理者権限でhostsファイルを上書きします。~~
~~```スタートボタン押下　メモ帳の検索　右クリックして「管理者権限で実行」 ```~~
~~- hostsのパスを開きます~~
~~```C:\Windows\System32\drivers\etc\hosts```~~
~~- hostsファイルに以下を追記します。~~
~~```127.0.0.1  my-local.test```~~
~~- 必ず再起動します。~~
~~```ipconfig /flushdns```~~

<!--
### ウェブサーバーの設定
- 取得した自己署名証明書をウェブサーバーに設定します。
- Apatchの場合
```
<VirtualHost *:443>
    ServerName my-local.test
    SSLEngine on
    SSLCertificateFile /path/to/my-local.crt
    SSLCertificateKeyFile /path/to/my-local.key
</VirtualHost>
```
-->
</details>

<details><summary>自己署名証明書を仮想サーバに組み込む</summary>

#### 自己署名証明書を仮想サーバに組み込む

- 自己署名証明書の生成: OpenSSLを使って、自己署名証明書を生成します。
1. カレントディレクトリに移動して生成します
2. activateする
   - ```.\env\Scripts\activate```
~~   - ```uvicorn main:app --reload```~~
3. uvicornを使ってHTTPSサーバーを起動
   - 生成した証明書と秘密鍵を使用して、uvicornでHTTPSサーバーを起動します。
   - ```uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt```
4. ブラウザからアクセスする
   - ```https://localhost:8000```
5. 自己署名証明書を信頼する: 自己署名証明書をローカルの信頼済み証明書ストアに追加することで、この警告を回避できます。
   - my-local.crtをダブルクリックして、証明書インストールウィザードを開きます。
</details>

<details><summary>備考</summary>

#### 備考
- k.okuma@ten-system.com
- https://ten-system.com/index.html
</details>

以上

