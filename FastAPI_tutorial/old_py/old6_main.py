from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()

class FormData(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}
 
@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data

# フォームデータ
# https://fastapi.tiangolo.com/ja/tutorial/request-forms/

'''
curl -X POST "http://127.0.0.1:8000/login/" -H "Content-Type: application/x-www-form-urlencoded" -d "username=testuser&password=testpassword"
'''
@app.post("/login/")
async def login(username: str = Form(), password: str = Form()):
    return {"username": username}