# router.py
from fastapi import FastAPI
from fastapi import APIRouter

router = APIRouter()

# 呼び方
# https://127.0.0.1:8000/api/items
@router.get("/items/")
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

'''
appがrouterに認識されない場合
1. __init__.pyをフォルダに必ず置く
2. PythonのPath設定方法
設定
setx PYTHONPATH "C:\Obento-Test\v_0.1.3\app"
確認
set PYTHONPATH
もしくは　sysdm.cpl
削除
setx PYTHONPATH ""
'''