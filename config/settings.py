"""프로젝트 설정 (환경변수 로드)."""
import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트 기준 .env 로드
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# Naver
NAVER_ID = os.getenv("NAVER_ID", "")
NAVER_PW = os.getenv("NAVER_PW", "")

# Bizno API
BIZNO_API_KEY = os.getenv("BIZNO_API_KEY", "")

# 실행 옵션
HEADLESS = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
MAX_PAGES_DEFAULT = int(os.getenv("MAX_PAGES_DEFAULT", "1"))

# URL
NAVER_SEARCH_BASE = "https://search.shopping.naver.com/search/all"
BIZNO_API_BASE = "https://bizno.net/api"  # 실제 API 베이스는 비즈노 문서 확인 필요
