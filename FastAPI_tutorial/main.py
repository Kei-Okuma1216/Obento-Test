# 備考 
# ここでインスタンスでなく関数注入をしている。
from typing import Union

from fastapi import Cookie, Depends, FastAPI

app = FastAPI()
# サブ依存関係
# https://fastapi.tiangolo.com/ja/tutorial/dependencies/sub-dependencies/#_2

from fastapi import Depends

async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()
        
async def dependency_a():
    dep_a = generate_dep_a()
    try:
        yield dep_a
    finally:
        dep_a.close()


async def dependency_b(dep_a=Depends(dependency_a)):
    dep_b = generate_dep_b()
    try:
        yield dep_b
    finally:
        dep_b.close(dep_a)


async def dependency_c(dep_b=Depends(dependency_b)):
    dep_c = generate_dep_c()
    try:
        yield dep_c
    finally:
        dep_c.close(dep_b)
        
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