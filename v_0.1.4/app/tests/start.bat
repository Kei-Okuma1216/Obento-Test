@echo off
REM cd /d "C:\Obento-Test\v_0.1.2\app\tests"
REM cd /d %~dp0  REM testsフォルダに移動
REM C:\Obento-Test\v_0.1.2\app\tests
REM pytest test_login3.py
REM pytest test_login3.py -s | tee pytest_results.log

REM ただし、pytest を実行するときのカレントディレクトリを app/ の外にする ってことだよ！💡
REM ✨ tests/ は app/ の中に置いたままでOK！移動しなくていいよ！ 👍
REM cd C:\Obento-Test\v_0.1.3\
REM pytest app/tests

REM uviconrの手動による起動
@echo off
chcp 65001  :: コマンドプロンプトの文字コードページをUTF-8
cd /d C:\Obento-Test\v_0.1.3\app
call .\env\Scripts\activate
start "" C:\Windows\System32\cmd.exe /k "uvicorn main:app --host 127.0.0.1 --port 8000 --ssl-keyfile=./my-local.key --ssl-certfile=./my-local.crt"

timeout /t 5 /nobreak
cd tests
pytest test_login4.py -o log_cli=true pytest_log.txt
pause
