
# FastAPI実装調査


## 
### 環境構築方法
```bash
pip install fastapi uvicorn
```

### 簡易テストコード実行方法
#### 仮想環境の作成

1. 実装調査パスを ```cmd``` で開く
```C:\Users\tensy\OneDrive\ドキュメント\okuma\お弁当注文システム\実装調査```
2. 仮想環境を作成
   ```python -m venv env```
3. 仮想環境をactivateする
   ```.\env\Scripts\activate```
4. 仮想環境を終了する
   ```deactivate```

#### 仮想環境での実行
5. 以下のappの含まれる```main.py```ファイルを配置する
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
6. コマンドプロンプトで実行する。
   ```uvicorn main:app --reload```
7. ブラウザで URLに移動する。
   ```http://127.0.0.1:8000```
   ```http://127.0.0.1:8000/items/1?q=test```
   ```http://127.0.0.1:8000/login/001?password=testPass```
8. 終了する
    ```Ctrl + C```
9. Edgeで開く
    ```"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" http://127.0.0.1:8000```

### 
#### 概要
- ユーザーは登録操作でサーバーから”シグネチャ”をもらう（シグネチャの中身はBase64Encode文字列）

#### 具体的な流れ
- 登録URLと注文URLは兼用である。
- もし注文URLのみでシグネチャを持っていない
   - 初期登録画面に遷移する。
- もし注文URLのみでシグネチャを持っている
   - 登録修正画面に遷移する。
- もし登録URL以外にアクセスする
   - アクセスエラーを表示する。
- 初期登録が正常に完了する
   - ユーザーにシグネチャを返す。
- ユーザーは自身のスマホに、シグネチャを保存する。

- ユーザーは注文URLにユーザーのシグネチャと数量を付加してアクセスする。
- サーバーはシグネチャを検証する
   - シグネチャが正しくない
      - エラーを表示する。　
   - シグネチャが正しい
      - 正常な注文処理とする。


Base64Encodingのつくりかた

1. httpsを必ず使う
2. 暗号化アルゴリズムをnone（署名なし）にしない
3. トークンのライフサイクルをできるだけ適切にしてリフレッシュする

#### OpenSSLのインストール
1. [ガイドを読む](https://atmarkit.itmedia.co.jp/ait/articles/1601/29/news043.html)
2. [OpenSSLインストーラー x64 exe light](https://slproweb.com/products/Win32OpenSSL.html)
3. Pathの設定
   Ctrl + R  SystemPropertiesAdvanced


以上

