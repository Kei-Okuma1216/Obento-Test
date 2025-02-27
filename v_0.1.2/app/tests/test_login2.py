# tests/test_login.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login_form():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/login")
        assert response.status_code == 200
        assert "form" in response.text

@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/login", data={"username": "test", "password": "password"})
        assert response.status_code == 200
        assert response.text == "Login Successful"

@pytest.mark.asyncio
async def test_login_failure():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/login", data={"username": "wrong", "password": "wrong"})
        assert response.status_code == 200
        assert response.text == "Login Failed"

@pytest.mark.asyncio
async def test_login_autofill():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/login", data={"username": "test", "password": "password"})
        assert response.status_code == 200
        assert "Login Successful" in response.text
