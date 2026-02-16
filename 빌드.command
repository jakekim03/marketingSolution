#!/bin/bash
cd "$(dirname "$0")"

echo "[1/3] 환경 확인..."
if [ ! -d ".venv" ]; then
  echo ".venv이 없습니다. 먼저 다음을 실행하세요:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
  echo "  .venv/bin/playwright install chromium"
  read -p "Enter로 종료."
  exit 1
fi

echo "[2/3] Chromium을 playwright_browsers 폴더에 설치..."
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/playwright_browsers"
mkdir -p playwright_browsers
.venv/bin/playwright install chromium
if [ $? -ne 0 ]; then
  echo "Chromium 설치 실패."
  read -p "Enter로 종료."
  exit 1
fi

echo "[3/3] PyInstaller로 앱 빌드..."
.venv/bin/pip install pyinstaller -q
.venv/bin/pyinstaller --noconfirm app.spec
if [ $? -ne 0 ]; then
  echo "빌드 실패."
  read -p "Enter로 종료."
  exit 1
fi

cp "실행방법_배포용.txt" "dist/법인영업솔루션/" 2>/dev/null || true
# Mac 사용자용: 더블클릭으로 실행할 수 있는 실행.command 생성
cat > "dist/법인영업솔루션/실행.command" << 'RUNNER'
#!/bin/bash
cd "$(dirname "$0")"
./법인영업솔루션
read -p "종료하려면 Enter를 누르세요."
RUNNER
chmod +x "dist/법인영업솔루션/실행.command" 2>/dev/null || true
echo ""
echo "완료. 실행 파일: dist/법인영업솔루션/법인영업솔루션"
echo "Mac: dist/법인영업솔루션/실행.command 더블클릭 (또는 터미널에서 ./법인영업솔루션)"
echo "폴더 전체를 ZIP으로 압축해 전달하면 됩니다."
read -p "Enter로 종료."
