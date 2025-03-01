import time
import pytest
import logging
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

# ログの設定
#logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
#logger = logging.getLogger(__name__)
# ログの設定（ファイルに出力）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",  # 出力ファイル名
    filemode="a",        # "w" なら毎回上書き、"a" なら追記
)
logger = logging.getLogger(__name__)

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
    logger.info(">>> サーバーを起動中...")
    server_process = subprocess.Popen(
        [
            "cmd.exe", "/c", "cd /d C:\\Obento-Test\\v_0.1.2\\app & .\\env\\Scripts\\activate & uvicorn main:app --host 127.0.0.1 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt"
        ],
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    time.sleep(15)  # サーバーが立ち上がるのを待つ（適宜調整）
    logger.info("サーバーが起動しました")

    yield

    logger.info(">>> サーバーを停止中...")
    #server_process.terminate()
    time.sleep(3)  # 停止を待つ
    logger.info(">>> サーバーを停止しました")

@pytest.fixture
def driver(server):   
    """ Edgeブラウザのセットアップ """
    logger.info(">>> EdgeDriverのインストールを開始")
    service = Service(EdgeChromiumDriverManager().install())

    logger.info(">>> Edgeのオプションを設定中")
    options = webdriver.EdgeOptions()
    # options.add_argument("--headless")  # GUI無しで実行する場合はコメント解除
    options.add_argument("--log-level=3")  # ログレベルを抑える
    options.add_argument("--ignore-certificate-errors")  # 証明書エラーを無視


    logger.info(">>> Edgeブラウザを起動")
    driver = webdriver.Edge(service=service, options=options)

    logger.info(">>> 要素の待機時間を設定")
    driver.implicitly_wait(5)  # 要素の待機時間

    logger.info(">>> Edge 起動後、15秒待機")
    time.sleep(15)
    logger.info(">>> 15秒待機 終了")
    
    logger.info(">>> ブラウザの準備が完了")
    yield driver

    logger.info(">>> ブラウザを閉じます")
    #driver.quit()

def test_login_page(driver):
    """ login.html に遷移できるか確認 """
    driver.get("https://127.0.0.1:8000")  # 適切なURLに変更

    driver.implicitly_wait(15) 
    
    assert "ログイン" in driver.title  # タイトルに「ログイン」が含まれるか


def test_login_button(driver):
    """ ログインボタンを押して遷移を確認 """
    driver.get("https://127.0.0.1:8000")
    
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
    assert driver.current_url == "https://127.0.0.1:8000/order_complete.html"