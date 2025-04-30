@echo off
chcp 65001 > nul
echo SMU 과제 수집기를 실행합니다...
echo 헤드리스 모드로 실행됩니다. 1주일 또는 2주일 마감 기간을 선택한 후 아이디와 비밀번호를 입력해주세요.
cd %~dp0
python src/main.py
pause