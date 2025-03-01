@echo off
REM cd /d "C:\Obento-Test\v_0.1.2\app\tests"
REM cd /d %~dp0  REM testsフォルダに移動
REM C:\Obento-Test\v_0.1.2\app\tests
REM pytest test_login3.py
REM pytest test_login3.py -s | tee pytest_results.log
pytest test_login4.py -o log_cli=true pytest_log.txt
pause
