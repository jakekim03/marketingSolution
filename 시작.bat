@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
  echo 가상환경이 없습니다. 먼저 아래를 명령 프롬프트에서 실행해 주세요:
  echo   python -m venv .venv
  echo   .venv\Scripts\activate
  echo   pip install -r requirements.txt
  echo   playwright install chromium
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python app.py
pause
