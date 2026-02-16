# 법인 영업 솔루션 (마케팅 솔루션)

네이버 스마트스토어 검색으로 상품 정보를 수집하고, **정보** 버튼에서 추출한 사업자등록번호를 [bizno.net](https://bizno.net)에서 조회해 **회사이름·사업자등록번호·회사이메일**을 엑셀로 저장하는 도구입니다.

---

## 일반 사용자(Windows)에게 배포할 때

**개발을 모르는 사람**에게 Git 저장소 링크만 주면 안 됩니다. 아래 순서대로 하세요.

### 1) Git에 소스 올리기

```bash
git add .
git commit -m "법인 영업 솔루션"
git remote add origin https://github.com/본인아이디/저장소이름.git
git push -u origin main
```

### 2) Windows에서 exe 빌드하기

- **Windows PC**가 필요합니다 (맥만 있으면 지인 PC·가상머신 등).
- 프로젝트 폴더를 압축 해제한 뒤:

| 방법 | 설명 |
|------|------|
| **setup_and_build.bat 더블클릭** | **Python 설치 없이** 한 번에 진행. Python을 자동으로 받아서 설치한 뒤 빌드까지 실행. (처음 1회 약 5~10분, 인터넷 필요) |
| **build.bat 더블클릭** | 이미 Python + .venv 설정이 되어 있을 때만 사용. |
| **명령 프롬프트에서 실행** | Win+R → `cmd` 입력 → Enter 후, `cd /d "프로젝트폴더경로"` 입력하고 `setup_and_build.bat` 또는 `build.bat` 입력. |

- **파이썬을 모르는 사람**은 **setup_and_build.bat**만 더블클릭하면 됩니다. (Python 자동 다운로드 후 빌드)
- 끝나면 **`dist\법인영업솔루션`** 폴더가 생깁니다.

### 3) ZIP 만들고 공유하기

**방법 A – GitHub Release 사용 (추천)**

1. GitHub 저장소 페이지 → **Releases** → **Create a new release**
2. 태그 예: `v1.0` 입력 후 **Publish release**
3. 아래 **Assets**에서 **Attach binaries** 클릭
4. **`dist\법인영업솔루션` 폴더 전체를 ZIP으로 압축**한 파일(예: `법인영업솔루션_윈도우.zip`)을 올립니다.
5. Release 저장 후 **Release 페이지 주소**를 사용자에게 보냅니다.  
   예: `https://github.com/본인아이디/저장소이름/releases/tag/v1.0`

**방법 B – 직접 전달**

- `dist\법인영업솔루션` 폴더를 ZIP으로 압축해 이메일·카톡·드라이브로 전달합니다.

### 4) 사용자에게 안내할 말

- **"아래 링크에서 ZIP 파일 받아서, 압축 풀고, 폴더 안의 법인영업솔루션.exe 더블클릭해서 쓰세요."**
- 자세한 설명이 필요하면 **`사용자_안내.md`** 내용을 복사해 보내거나, GitHub에 올려둔 **사용자_안내.md** 링크를 같이 보내면 됩니다.

| 보낼 것 | 설명 |
|--------|------|
| **ZIP 다운로드 링크** | Release 페이지 또는 드라이브/전달 링크 |
| **사용자_안내.md** | 다운로드·압축 풀기·실행·사용 순서 정리된 안내 (이 저장소에 있음) |

> **일반 사용자(Windows)**: 소스 코드 말고 **Releases**에 올린 **Windows용 ZIP**을 받아서 사용하세요.  
> 사용 방법은 **[사용자_안내.md](./사용자_안내.md)** 를 보세요.

---

## 기능

1. **네이버 수동 로그인** (브라우저에서 로그인 후 터미널에서 Enter) → 쇼핑 검색
2. **키워드 검색** + 정렬 선택 (랭킹순, 낮은/높은 가격순, 리뷰 많은/좋은순, 등록일순)
3. **페이지 수 지정** 후 검색 결과에서 상품별 **정보** 버튼 클릭 → `layer_desc__Juas1` 값 수집
4. 수집한 값으로 **비즈노 API** 사업자 정보 조회
5. 결과 **CSV 저장**

## 환경 설정

### 1. 가상환경 및 패키지

```bash
cd marketingSolution
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. 환경 변수 (.env)

`.env.example`을 복사해 `.env`를 만들고 값을 채웁니다.

```bash
cp .env.example .env
```

- `BIZNO_API_KEY`: [비즈노 API](https://bizno.net/openapi) 발급 키 (사업자 조회 시 필수)
- `HEADLESS`: `true`면 브라우저 창 숨김
- `MAX_PAGES_DEFAULT`: 기본 수집 페이지 수

### 3. 비즈노 API

- 무료: 1일 200건, 사업자등록번호/상호명 검색 → 사업자등록번호, 상호명, 사업자상태, 과세유형
- 유료: 일괄조회, 대표자·전화번호·주소 등 추가 정보

실제 엔드포인트/파라미터는 [비즈노 API 문서](https://api.bizno.net/)에 맞게 `src/bizno/api.py`에서 수정해야 할 수 있습니다.

## 실행 방법

### 비개발자용 (웹에서 사용)

**처음 한 번만** 개발자 또는 관리자가 터미널에서 아래를 실행해 두세요.

```bash
cd marketingSolution
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# .env 에 BIZNO_API_KEY 필요 시 입력
```

이후에는 **더블클릭만** 하면 됩니다.

| 사용 환경 | 실행 방법 |
|-----------|-----------|
| **Mac** | `시작.command` 더블클릭 → 터미널 창이 뜨고 곧 브라우저가 열림. **터미널 창을 닫지 마세요.** |
| **Windows** | `시작.bat` 더블클릭 → 명령 창이 뜨고 곧 브라우저가 열림. **명령 창을 닫지 마세요.** |

브라우저에서 **키워드·정렬·페이지 수** 입력 후 **시작하기** → 뒤에 뜬 창에서 **네이버 로그인** → 웹 페이지에서 **로그인 완료했어요 → 수집 시작** 클릭 → 끝나면 **엑셀 파일 다운로드**로 저장합니다.

---

### 비개발자에게 그냥 전달 (exe/앱 빌드 – 설치 없이 실행)

Python을 설치하지 않은 사람에게 **실행 파일만 더블클릭해서 쓰게** 하려면, 한 번만 빌드한 뒤 **빌드 결과 폴더 전체**를 전달하면 됩니다.

| 환경 | 빌드 방법 | 결과물 | 친구가 실행하는 방법 |
|------|-----------|--------|----------------------|
| **Windows** | `빌드.bat` 더블클릭 (또는 cmd에서 `빌드.bat` 실행) | `dist\법인영업솔루션\법인영업솔루션.exe` | 폴더 압축 해제 후 **법인영업솔루션.exe** 더블클릭 |
| **Mac** | `빌드.command` 더블클릭 (처음엔 우클릭 → 열기) | `dist/법인영업솔루션/법인영업솔루션` | 폴더 압축 해제 후 터미널에서 `./법인영업솔루션` 또는 **법인영업솔루션** 더블클릭 |

1. **빌드 (개발자 PC에서 한 번만)**  
   - Windows: `빌드.bat` 실행 (명령 프롬프트에서 실행하면 됨)  
   - Mac: `빌드.command` 더블클릭 (첫 실행 시 **우클릭 → 열기**로 실행 허용)  
   - 완료 후 `dist/법인영업솔루션` 폴더가 생김 (약 300MB 내외, Chromium 포함)

2. **배포**  
   - `dist/법인영업솔루션` 폴더 전체를 ZIP으로 압축해서 전달

3. **친구가 할 일**  
   - ZIP 풀기 → Windows는 **법인영업솔루션.exe** 더블클릭, Mac은 **법인영업솔루션** 실행 (또는 터미널에서 `./법인영업솔루션`)  
   - Python·가상환경·pip 설치 없이 실행됨

---

### 개발자용 (터미널 명령)

프로젝트 루트에서 실행합니다.

```bash
# 기본: 키워드만 (1페이지, 랭킹순, 비즈노 조회)
python -m src.main 마스크팩

# 정렬: 리뷰 많은순, 2페이지 수집
python -m src.main 마스크팩 --sort 리뷰많은순 --pages 2

# 정렬 옵션: 랭킹, 낮은가격, 높은가격, 리뷰많은순, 리뷰좋은순, 등록일순
python -m src.main 마스크팩 --sort 낮은가격 --pages 1

# 비즈노 조회 없이 정보값만 수집
python -m src.main 마스크팩 --skip-bizno

# 결과 파일 지정
python -m src.main 마스크팩 -o data/마스크팩_결과.csv

# 브라우저 숨김
python -m src.main 마스크팩 --headless
```

## 프로젝트 구조

```
marketingSolution/
├── app.py                # 웹 실행 (비개발자용)
├── 시작.command          # Mac 더블클릭 실행
├── 시작.bat              # Windows 더블클릭 실행
├── config/
│   └── settings.py       # 환경변수 로드
├── src/
│   ├── naver/
│   │   ├── constants.py  # 정렬 옵션, 셀렉터
│   │   ├── login.py      # 네이버 로그인
│   │   ├── search.py     # 검색 URL 생성
│   │   └── scraper.py    # 정보 버튼 클릭 및 값 수집
│   ├── bizno/
│   │   └── api.py        # 비즈노 API 클라이언트
│   └── main.py           # CLI 진입점
├── data/                 # 결과 CSV 저장
├── .env.example
├── requirements.txt
└── README.md
```

## 주의사항

- **로그인은 수동**입니다. (웹 사용 시: 뒤에 뜬 브라우저 창에서 로그인 후, 웹 페이지의 **로그인 완료했어요** 버튼 클릭)
- 네이버 쇼핑 페이지 HTML이 바뀌면 `src/naver/constants.py`의 `SELECTOR_BTN_INFO`, `SELECTOR_LAYER_DESC`를 실제 구조에 맞게 수정해야 합니다.
- 비즈노 무료 API는 **1일 200건** 제한이 있으므로, 많은 건수 수집 시 유료 API 또는 캐싱/배치 설계를 고려하세요.
