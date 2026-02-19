# 법인 영업 솔루션 (마케팅 솔루션)

네이버 스마트스토어 검색으로 상품 정보를 수집하고, **정보** 버튼에서 추출한 사업자등록번호를 [bizno.net](https://bizno.net)에서 조회해 **회사이름·사업자등록번호·회사이메일**을 엑셀로 저장하는 도구입니다.

---

## 실행 방법 (IDE에서 폴더 열고 실행)

1. **Cursor** 또는 **VS Code**를 설치한 뒤, 이 **프로젝트 폴더**를 연다 (파일 → 폴더 열기).
2. **Python** 설치: [python.org](https://www.python.org/downloads/) (Windows는 설치 시 "Add to PATH" 체크).
3. **처음 한 번만** 터미널에서 패키지 설치:
   - **Mac:**  
     `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -r requirements.txt` → `playwright install chromium`
   - **Windows:**  
     `python -m venv .venv` → `.venv\Scripts\activate` → `pip install -r requirements.txt` → `playwright install chromium`
4. **실행:** `app.py`를 연 뒤 **F5** 또는 **실행 버튼** 클릭.  
   또는 터미널에서: `python app.py` (Windows), `python3 app.py` (Mac)
5. 브라우저가 열리면 웹 화면대로 사용하면 된다.

> **미리 받을 것·한 번 설정:** [미리_다운받기.md](./미리_다운받기.md) 참고.

---

## 기능

1. **네이버 수동 로그인** (브라우저에서 로그인) → 쇼핑 검색
2. **키워드 검색** + 정렬 선택 (랭킹순, 낮은/높은 가격순, 리뷰 많은/좋은순, 등록일순)
3. 검색 결과에서 상품별 **정보** 버튼 클릭 → 사업자번호 등 수집
4. 수집한 값으로 **비즈노** 사업자 정보 조회
5. 결과 **엑셀 저장**

---

## 환경 설정

### .env

`.env.example`을 복사해 `.env`를 만들고 값을 채운다.

```bash
cp .env.example .env
```

- `BIZNO_API_KEY`: [비즈노 API](https://bizno.net/openapi) 발급 키 (사업자 조회 시 필수)
- `HEADLESS`: `true`면 브라우저 창 숨김
- `MAX_PAGES_DEFAULT`: 기본 수집 페이지 수

### 비즈노 API

- 무료: 1일 200건 등 제한 있음.  
- 실제 엔드포인트/파라미터는 [비즈노 API 문서](https://api.bizno.net/)에 맞게 `src/bizno_net` 등에서 수정할 수 있다.

---

## 프로젝트 구조

```
marketingSolution/
├── app.py              # 웹 실행 진입점 (IDE에서 F5로 실행)
├── config/
├── src/
│   ├── naver/          # 검색, 스크래핑
│   └── bizno_net.py    # 사업자 조회
├── data/               # 결과 엑셀 저장
├── .env.example
├── requirements.txt
├── 미리_다운받기.md
└── README.md
```

---

## 주의사항

- **로그인은 수동**: 브라우저 창에서 네이버 로그인 후, 웹 페이지의 **로그인 완료했어요** 버튼 클릭.
- 네이버 쇼핑 HTML이 바뀌면 `src/naver/` 셀렉터를 수정해야 할 수 있다.
- 비즈노 무료 API는 1일 200건 제한 등이 있음.
