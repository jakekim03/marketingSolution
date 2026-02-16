@echo off
cd /d "%~dp0"

echo [1/3] Checking .venv...
if not exist ".venv\Scripts\activate.bat" (
  echo ERROR: .venv not found. Run these in cmd first:
  echo   python -m venv .venv
  echo   .venv\Scripts\activate
  echo   pip install -r requirements.txt
  echo   playwright install chromium
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat

echo [2/3] Installing Chromium to playwright_browsers...
set PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers
if not exist "playwright_browsers" mkdir "playwright_browsers"
playwright install chromium
if errorlevel 1 (
  echo ERROR: Chromium install failed.
  pause
  exit /b 1
)

echo [3/3] Building exe with PyInstaller...
pip install pyinstaller --quiet
pyinstaller --noconfirm app.spec
if errorlevel 1 (
  echo ERROR: Build failed.
  pause
  exit /b 1
)

if exist "사용방법_배포용.txt" (
  copy /Y "%~dp0사용방법_배포용.txt" "dist\MarketingSolution\사용방법.txt" >nul 2>&1
)

echo.
echo ====== Done ======
echo.
echo  Output folder: dist\MarketingSolution
echo  Zip that folder and send. User runs MarketingSolution.exe
echo.
pause
