@echo off
chcp 65001 > nul
echo SMU 과제 수집기를 실행합니다...
cd %~dp0
python src/main.py
pause