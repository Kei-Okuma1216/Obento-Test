import time
import pytest
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
#from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# インストール
#pip install pytest selenium webdriver-manager
# 実行方法
# pytest tests/test_login.py
'''
@pytest.fixture
def driver():
    """ Chromeブラウザのセットアップ """
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")  # GUI無しで実行
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)  # 要素の待機時間
    yield driver
    driver.quit()
'''
@pytest.fixture(scope="session")
def server():
    """ uvicorn を起動し、テストが終わったら停止する """
    print(">>> サーバーを起動中...")
    server_process = subprocess.Popen(
        [
            "cmd.exe", "/k", "cd /d C:\\Obento-Test\\v_0.1.2\\app & .\\env\\Scripts\\activate & uvicorn main:app --host 127.0.0.1 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt"
        ],
        shell=True
    )
    time.sleep(5)  # サーバーが立ち上がるのを待つ（適宜調整）
    yield
    print(">>> サーバーを停止中...")
    server_process.terminate()

'''
@pytest.fixture
def driver(server):
    subprocess.run('C:\Windows\System32\cmd.exe /k "cd /d C:\Obento-Test\v_0.1.2\app & .\env\Scripts\activate & uvicorn main:app --host 127.0.0.1 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt"', shell=True)  # コマンドプロンプトを開いたまま実行
    
    """ Edgeブラウザのセットアップ """
    print(">>> EdgeDriverのインストールを開始")
    service = Service(EdgeChromiumDriverManager().install())
    
    print(">>> コマンドプロンプトを起動してコマンドを実行")
    #subprocess.run('cmd.exe /k "echo Hello from CMD & dir"', shell=True)  # コマンドプロンプトを開いたまま実行
    
    
    print(">>> Edgeのオプションを設定中")
    options = webdriver.EdgeOptions()
    # options.add_argument("--headless")  # GUI無しで実行する場合はコメント解除
    print(">>> Edgeブラウザを起動")
    driver = webdriver.Edge(service=service, options=options)
    print(">>> 要素の待機時間を設定")
    driver.implicitly_wait(5)  # 要素の待機時間
    print(">>> ブラウザの準備が完了")
    yield driver
    print(">>> ブラウザを閉じます")
    driver.quit()

    # コマンドの実行
    # C:\Windows\System32\cmd.exe /k "cd /d C:\Obento-Test\v_0.1.2\app & .\env\Scripts\activate & uvicorn main:app --host 127.0.0.1 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt"

def test_login_page(driver):
    """ login.html に遷移できるか確認 """
    driver.get("http://127.0.0.1:8000")  # 適切なURLに変更
    #driver.get("http://localhost:8000/")  # 適切なURLに変更
    assert "ログイン" in driver.title  # タイトルに「ログイン」が含まれるか

def test_login_button(driver):
    """ ログインボタンを押して遷移を確認 """
    driver.get("http://localhost:8000/login.html")  # 適切なURLに変更
    
    username = driver.find_element(By.NAME, "username")
    password = driver.find_element(By.NAME, "password")

    username.send_keys("user1")
    password.send_keys("user1")

    # ログインボタンを取得
    login_button = driver.find_element(By.ID, "login-button")  # 適切なIDを設定

    # ボタンをクリック
    login_button.click()

    time.sleep(2)  # ページ遷移待機（適宜変更）

    # 遷移後のURLを確認（適切なURLに変更）
    assert driver.current_url == "http://localhost:8000/dashboard.html"
'''