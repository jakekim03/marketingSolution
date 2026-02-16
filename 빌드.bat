@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] 가상환경 확인...
if not exist ".venv\Scripts\activate.bat" (
  echo .venv이 없습니다. 먼저 다음을 실행하세요:
  echo   python -m venv .venv
  echo   .venv\Scripts\activate
  echo   pip install -r requirements.txt
  echo   playwright install chromium
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat

echo [2/3] Chromium을 playwright_browsers 폴더에 설치...
set PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers
if not exist "playwright_browsers" mkdir playwright_browsers
playwright install chromium
if errorlevel 1 (
  echo Chromium 설치 실패. 수동: set PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers ^& playwright install chromium
  pause
  exit /b 1
)

echo [3/3] PyInstaller로 exe 빌드...
pip install pyinstaller --quiet
pyinstaller --noconfirm app.spec
if errorlevel 1 (
  echo 빌드 실패.
  pause
  exit /b 1
)

copy /Y "%~dp0사용방법_배포용.txt" "dist\법인영업솔루션\사용방법.txt" >nul 2>&1
echo.
echo ====== 완료 ======
echo.
echo  [보낼 것]  dist\법인영업솔루션  폴더 전체를 ZIP으로 압축
echo             (또는 폴더를 그대로 전달)
echo.
echo  [받는 사람]  ZIP 압축 해제 후 "법인영업솔루션.exe" 더블클릭
echo               (Python 등 설치 필요 없음)
echo.
pause
