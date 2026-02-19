@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
  echo .venv not found. In cmd run: python -m venv .venv
  echo   then: .venv\Scripts\activate
  echo   then: pip install -r requirements.txt
  echo   then: playwright install chromium
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python app.py
pause
