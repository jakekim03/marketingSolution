#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "가상환경이 없습니다. 터미널을 열고 이 폴더에서 아래를 순서대로 실행해 주세요:"
  echo ""
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
  echo "  .venv/bin/playwright install chromium"
  echo ""
  read -p "종료하려면 Enter를 누르세요."
  exit 1
fi

# Flask 등 패키지가 없으면 자동 설치
if ! .venv/bin/python -c "import flask" 2>/dev/null; then
  echo "필요한 패키지를 설치하는 중입니다 (처음 한 번만)..."
  .venv/bin/pip install -r requirements.txt
  .venv/bin/playwright install chromium
  echo "설치 완료. 다시 실행합니다."
  echo ""
fi

.venv/bin/python app.py
read -p "종료하려면 Enter를 누르세요."
