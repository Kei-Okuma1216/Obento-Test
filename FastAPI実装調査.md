
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


###  余談 Clickイベントの書き方も、現在の最新はこうだ。
[Element: click イベント](https://developer.mozilla.org/ja/docs/Web/API/Element/click_event?form=MG0AV3)





以上

