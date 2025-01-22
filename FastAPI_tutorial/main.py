# 備考 
# ここでインスタンスでなく関数注入をしている。
from ssl import SSLSession
from typing import Union

from fastapi import Cookie, Depends, FastAPI

app = FastAPI()
# サブ依存関係
# https://fastapi.tiangolo.com/ja/tutorial/dependencies/sub-dependencies/#_2

from fastapi import Depends

async def get_db():
    db = SSLSession()
    try:
        yield db
    finally:
        db.close()

# TODO: generate_dep_a, generate_dep_b, generate_dep_c の実装が必要
async def dependency_a() -> void:
    dep_a = generate_dep_a()
    try:
        yield dep_a
    finally:
        dep_a.close()


async def dependency_b(dep_a=Depends(dependency_a)):
    try:
        dep_b = generate_dep_b()
        yield dep_b
    except Exception as e:
        # エラーログの記録
        print(f"Error in dependency_b: {e}")
        raise
    finally:
        dep_b.close(dep_a)


async def dependency_c(dep_b=Depends(dependency_b)):
    try:
        dep_c = generate_dep_c()
        yield dep_c
    except Exception as e:
        # エラーログの記録
        print(f"Error in dependency_b: {e}")
        raise
    finally:
        dep_c.close(dep_b)
'''     
class MySuperContextManager:
    def __init__(self):
        self.db = DBSession()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()


async def get_db():
    with MySuperContextManager() as db:
        yield db
        '''