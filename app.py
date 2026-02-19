"""
법인 영업 솔루션 - 웹 실행 (비개발자용).
Playwright는 한 스레드에서만 사용하므로, 전용 워커 스레드에서 브라우저를 실행합니다.
네이버 쇼핑에서 사업자번호 수집 → bizno.net에서 회사이름·이메일 조회 → 엑셀 다운로드.

exe로 실행 시: ROOT = exe 있는 폴더, Chromium은 playwright_browsers 폴더 사용.
"""
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from pathlib import Path

from flask import Flask, request, url_for, send_file, jsonify, redirect
from openpyxl import Workbook

# exe(빌드)로 실행 중이면 exe 있는 폴더를 루트로. PyInstaller 6+는 데이터를 _internal 에 넣음
if getattr(sys, "frozen", False):
    _exe_dir = Path(sys.executable).resolve().parent
    _internal = _exe_dir / "_internal"
    ROOT = _internal if _internal.is_dir() else _exe_dir
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(ROOT / "playwright_browsers")

    def _ensure_browser_executable():
        """번들에서 추출된 Chromium 실행 가능하도록: 권한 부여, macOS 격리 제거·서명."""
        browsers_dir = ROOT / "playwright_browsers"
        if not browsers_dir.is_dir():
            return
        for d in browsers_dir.iterdir():
            if not d.is_dir() or not d.name.startswith("chromium-"):
                continue
            # 모든 파일/디렉터리에 실행(탐색) 권한 부여
            for f in d.rglob("*"):
                try:
                    mode = f.stat().st_mode
                    os.chmod(f, mode | (0o111 if f.is_file() else 0o111))
                except OSError:
                    pass
            # macOS: 격리 속성 제거 (다운로드 등으로 실행 차단되는 것 방지)
            if sys.platform == "darwin":
                try:
                    subprocess.run(
                        ["xattr", "-cr", str(d)],
                        capture_output=True,
                        timeout=10,
                    )
                except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                    pass
                # Chromium.app ad-hoc 서명 (서명 없으면 spawn EACCES 발생할 수 있음)
                chromium_app = d / "chrome-mac" / "Chromium.app"
                if chromium_app.is_dir():
                    try:
                        subprocess.run(
                            ["codesign", "--force", "--deep", "--sign", "-", str(chromium_app)],
                            capture_output=True,
                            timeout=60,
                        )
                    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                        pass
    _ensure_browser_executable()
else:
    ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

from src.naver.constants import SORT_OPTIONS
from src.naver.scraper import scrape_search_results
from src.naver.search import get_sort_display_name
from src.bizno_net import scrape_company_info

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024

# 워커 스레드에 보낼 작업 큐 (action, payload, result_queue)
_cmd_queue = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()

# 수집 진행 상태 (job_id -> { status, results: [{회사이름, 사업자등록번호, 회사이메일주소}], filepath, enrich_total, error })
_jobs = {}
_jobs_lock = threading.Lock()


def _playwright_worker():
    """Playwright는 이 스레드에서만 실행 (스레드 전환 오류 방지)."""
    from playwright.sync_api import sync_playwright

    playwright = None
    browser = None
    page = None

    while True:
        try:
            cmd = _cmd_queue.get()
            if cmd is None:
                break
            action, payload, result_queue = cmd
            try:
                if action == "start":
                    if browser:
                        try:
                            browser.close()
                        except Exception:
                            pass
                    if playwright:
                        try:
                            playwright.stop()
                        except Exception:
                            pass
                    playwright = sync_playwright().start()
                    browser = playwright.chromium.launch(headless=False)
                    context = browser.new_context(
                        locale="ko-KR",
                        viewport={"width": 1280, "height": 720},
                    )
                    page = context.new_page()
                    page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
                    page.wait_for_load_state("networkidle", timeout=30000)
                    result_queue.put(("ok", None))

                elif action == "go_search":
                    if not page:
                        result_queue.put(("error", RuntimeError("브라우저가 없습니다. 처음부터 다시 시작해 주세요.")))
                    else:
                        from src.naver.search import build_search_url
                        url = build_search_url(
                            query=payload["keyword"],
                            sort_key=payload["sort_key"],
                            paging_index=1,
                        )
                        page.goto(url, wait_until="domcontentloaded")
                        page.wait_for_load_state("networkidle", timeout=30000)
                        result_queue.put(("ok", None))

                elif action == "run":
                    if not page:
                        result_queue.put(("error", RuntimeError("브라우저가 없습니다. 처음부터 다시 시작해 주세요.")))
                    else:
                        progress_queue = payload.get("progress_queue")
                        # 1) 네이버 쇼핑에서 사업자번호만 수집 (중복 제외)
                        info_values = scrape_search_results(
                            page,
                            query=payload["keyword"],
                            sort_key=payload["sort_key"],
                            max_count=payload.get("max_count", 50),
                            already_logged_in=True,
                            already_on_first_page=payload.get("already_on_first_page", False),
                            on_item=None,
                        )
                        # 2) bizno.net/article/{bizno} 열어서 회사이름·회사이메일 조회
                        if progress_queue is not None:
                            progress_queue.put(("enrich_start", len(info_values)))
                        for bizno in info_values:
                            name, email = scrape_company_info(page, bizno)
                            if progress_queue is not None:
                                progress_queue.put((name or "", bizno, email or ""))
                        if progress_queue is not None:
                            progress_queue.put(None)
                        result_queue.put(("ok", info_values))

                elif action == "close":
                    if browser:
                        try:
                            browser.close()
                        except Exception:
                            pass
                        browser = None
                    if playwright:
                        try:
                            playwright.stop()
                        except Exception:
                            pass
                        playwright = None
                    result_queue.put(("ok", None))
            except Exception as e:
                result_queue.put(("error", e))
        except Exception:
            pass


def _ensure_worker():
    global _worker_started
    with _worker_lock:
        if not _worker_started:
            t = threading.Thread(target=_playwright_worker, daemon=True)
            t.start()
            _worker_started = True


def _send_cmd(action: str, payload: dict, timeout: float = 600):
    _ensure_worker()
    result_queue = queue.Queue()
    _cmd_queue.put((action, payload, result_queue))
    status, data = result_queue.get(timeout=timeout)
    if status == "error":
        raise data
    return data


def _html_head(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ font-family: 'Malgun Gothic', sans-serif; max-width: 520px; margin: 40px auto; padding: 0 20px; }}
    h1 {{ font-size: 1.3rem; color: #03c75a; }}
    label {{ display: block; margin-top: 12px; font-weight: bold; }}
    input, select {{ width: 100%; padding: 8px; margin-top: 4px; box-sizing: border-box; }}
    button, .btn {{ display: inline-block; margin-top: 16px; padding: 12px 24px; background: #03c75a; color: #fff; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 1rem; }}
    button:hover, .btn:hover {{ background: #02a84a; color: #fff; }}
    .msg {{ margin: 16px 0; padding: 12px; background: #f0f8f0; border-radius: 6px; }}
    .error {{ background: #fff0f0; }}
    .loading {{ color: #666; }}
  </style>
</head>
<body>"""


def _html_foot() -> str:
    return "</body></html>"


@app.route("/")
def index():
    sort_options_html = "".join(
        f'<option value="{k}">{get_sort_display_name(k)}</option>'
        for k in SORT_OPTIONS
    )
    return _html_head("법인 영업 솔루션") + f"""
  <h1>법인 영업 솔루션</h1>
  <p>키워드로 네이버 쇼핑 검색 후, 상품별 사업자 정보를 수집합니다.</p>
  <form method="post" action="{url_for('start')}">
    <label>검색 키워드</label>
    <input type="text" name="keyword" placeholder="예: 마스크팩" required>
    <label>정렬</label>
    <select name="sort">{sort_options_html}</select>
    <label>수집할 개수</label>
    <input type="number" name="max_count" value="50" min="1" max="500" placeholder="50">
    <button type="submit">시작하기</button>
  </form>
""" + _html_foot()


@app.route("/start", methods=["POST"])
def start():
    keyword = (request.form.get("keyword") or "").strip()
    sort_key = request.form.get("sort") or "랭킹"
    try:
        max_count = int(request.form.get("max_count") or "50")
        max_count = max(1, min(500, max_count))
    except ValueError:
        max_count = 50
    if not keyword:
        return _html_head("오류") + '<div class="msg error">키워드를 입력하세요.</div><a href="/" class="btn">돌아가기</a>' + _html_foot()

    sort_key = sort_key if sort_key in SORT_OPTIONS else "랭킹"

    try:
        _send_cmd("close", {}, timeout=10)
    except Exception:
        pass
    try:
        _send_cmd("start", {}, timeout=60)
    except Exception as e:
        return _html_head("오류") + f'<div class="msg error">브라우저 실행 실패: {e}</div><a href="/" class="btn">돌아가기</a>' + _html_foot()

    return _html_head("로그인") + f"""
  <h1>네이버 로그인</h1>
  <div class="msg">
    <strong>뒤에 뜬 브라우저 창</strong>에서 아래를 <strong>순서대로</strong> 모두 완료한 뒤, 맨 아래 버튼을 눌러주세요.
    <ul>
      <li>네이버 아이디·비밀번호 입력 후 로그인</li>
      <li><strong>보안 자동입력방지</strong>(캡차/퀴즈)가 뜨면 반드시 풀고 통과하기</li>
      <li>로그인된 메인 화면(네이버 첫 페이지)이 보인 뒤에만 아래 버튼 클릭</li>
    </ul>
  </div>
  <div class="msg loading">아래 버튼을 누르면 <strong>검색 화면</strong>으로 이동합니다. (바로 수집하지 않습니다)</div>
  <form method="post" action="{url_for('go_search')}">
    <input type="hidden" name="keyword" value="{keyword}">
    <input type="hidden" name="sort" value="{sort_key}">
    <input type="hidden" name="max_count" value="{max_count}">
    <button type="submit">로그인 완료했어요 → 다음</button>
  </form>
""" + _html_foot()


@app.route("/go_search", methods=["POST"])
def go_search():
    """검색 페이지로만 이동 (보안 확인 풀 수 있도록 한 단계 끊음)."""
    keyword = (request.form.get("keyword") or "").strip()
    sort_key = request.form.get("sort") or "랭킹"
    try:
        max_count = int(request.form.get("max_count") or "50")
        max_count = max(1, min(500, max_count))
    except ValueError:
        max_count = 50
    if not keyword:
        return _html_head("오류") + '<div class="msg error">키워드를 입력하세요.</div><a href="/" class="btn">돌아가기</a>' + _html_foot()
    sort_key = sort_key if sort_key in SORT_OPTIONS else "랭킹"

    try:
        _send_cmd("go_search", {"keyword": keyword, "sort_key": sort_key, "max_count": max_count}, timeout=30)
    except Exception as e:
        return _html_head("오류") + f'<div class="msg error">검색 페이지 이동 실패: {e}</div><a href="/" class="btn">돌아가기</a>' + _html_foot()

    return _html_head("보안 확인") + f"""
  <h1>보안 자동입력방지</h1>
  <div class="msg">
    브라우저에 <strong>검색 결과 화면</strong>이 떴을 거예요. 이때 <strong>보안 자동입력방지</strong>(캡차/퀴즈)가 보이면
    <strong>반드시 풀고 통과</strong>한 뒤, 검색 결과가 보이는 상태에서 아래 버튼을 눌러 주세요.
  </div>
  <div class="msg loading">버튼을 누르면 수집이 시작됩니다. 1~5분 걸릴 수 있으니 기다려 주세요.</div>
  <form method="post" action="{url_for('run')}" id="runForm">
    <input type="hidden" name="keyword" value="{keyword}">
    <input type="hidden" name="sort" value="{sort_key}">
    <input type="hidden" name="max_count" value="{max_count}">
    <button type="submit" id="submitBtn">보안 확인 완료했어요 → 수집 시작</button>
  </form>
  <script>
    document.getElementById('runForm').onsubmit = function() {{
      var btn = document.getElementById('submitBtn');
      btn.disabled = true;
      btn.textContent = '수집 중입니다... (1~5분 걸릴 수 있어요)';
    }};
  </script>
""" + _html_foot()


def _consumer_thread(progress_queue, filepath, job_id):
    """progress_queue에서 (회사이름, 사업자등록번호, 회사이메일) 받아서 엑셀에 추가·job 결과 반영. None 수신 시 저장 후 종료."""
    wb = Workbook()
    ws = wb.active
    ws.title = "기업정보"
    ws.append(["회사이름", "사업자등록번호", "회사이메일주소"])
    while True:
        try:
            item = progress_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        if item is None:
            break
        if isinstance(item, tuple) and len(item) == 2 and item[0] == "enrich_start":
            with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["enrich_total"] = item[1]
            continue
        if isinstance(item, tuple) and len(item) == 3:
            name, bizno, email = item
            row = {"회사이름": name or "", "사업자등록번호": bizno or "", "회사이메일주소": email or ""}
            ws.append([row["회사이름"], row["사업자등록번호"], row["회사이메일주소"]])
            with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["results"].append(row)
    try:
        wb.save(filepath)
    except Exception:
        pass


def _job_runner_thread(job_id, keyword, sort_key, max_count):
    """백그라운드에서 수집 실행. 끝나면 progress_queue에 __done__ 넣고 job 상태 갱신."""
    progress_queue = queue.Queue()
    data_dir = ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in keyword if c.isalnum() or c in " _-") or "result"
    fname = f"result_{safe_name}_{uuid.uuid4().hex[:8]}.xlsx"
    filepath = data_dir / fname
    with _jobs_lock:
        _jobs[job_id]["filepath"] = fname
    t = threading.Thread(target=_consumer_thread, args=(progress_queue, filepath, job_id), daemon=True)
    t.start()
    try:
        _send_cmd(
            "run",
            {
                "keyword": keyword,
                "sort_key": sort_key,
                "max_count": max_count,
                "already_on_first_page": True,
                "progress_queue": progress_queue,
            },
            timeout=900,
        )
    except Exception as e:
        with _jobs_lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(e)
    finally:
        progress_queue.put(None)
        t.join(timeout=5)
        try:
            _send_cmd("close", {}, timeout=10)
        except Exception:
            pass
        with _jobs_lock:
            if _jobs[job_id]["status"] == "running":
                _jobs[job_id]["status"] = "done"


@app.route("/run", methods=["POST"])
def run():
    keyword = (request.form.get("keyword") or "").strip()
    sort_key = request.form.get("sort") or "랭킹"
    try:
        max_count = int(request.form.get("max_count") or "50")
        max_count = max(1, min(500, max_count))
    except ValueError:
        max_count = 50
    sort_key = sort_key if sort_key in SORT_OPTIONS else "랭킹"

    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {"status": "running", "results": [], "filepath": None, "enrich_total": None, "error": None}
    t = threading.Thread(target=_job_runner_thread, args=(job_id, keyword, sort_key, max_count), daemon=True)
    t.start()
    return redirect(url_for("progress", job_id=job_id))


@app.route("/progress/<job_id>")
def progress(job_id):
    """수집 진행 페이지. 폴링으로 회사이름·사업자등록번호·회사이메일 목록 실시간 표시."""
    return _html_head("수집 중") + f"""
  <h1>수집 중</h1>
  <div class="msg" id="status">네이버 수집 및 bizno.net 조회 중…</div>
  <div class="msg">
    <strong>수집 목록 (회사이름 · 사업자등록번호 · 회사이메일주소)</strong>
    <ul id="list" style="max-height:320px; overflow-y:auto; margin:8px 0; list-style:none; padding-left:0;"></ul>
  </div>
  <div id="doneArea" style="display:none;">
    <a href="/" class="btn">다시 검색</a>
  </div>
  <script>
    var jobId = "{job_id}";
    function poll() {{
      fetch("/progress/status/" + jobId)
        .then(r => r.json())
        .then(function(data) {{
          var list = document.getElementById("list");
          list.innerHTML = "";
          if (data.results && data.results.length) {{
            var total = data.enrich_total ? data.enrich_total + "건 조회 중" : "";
            document.getElementById("status").innerHTML = "수집된 항목: <strong>" + data.results.length + "</strong>건 " + (total ? "(" + total + ")" : "");
            data.results.forEach(function(r) {{
              var li = document.createElement("li");
              li.style.padding = "4px 0";
              li.style.borderBottom = "1px solid #eee";
              li.textContent = (r.회사이름 || "-") + " · " + (r.사업자등록번호 || "-") + " · " + (r.회사이메일주소 || "-");
              list.appendChild(li);
            }});
          }} else {{
            document.getElementById("status").textContent = data.enrich_total ? "bizno.net 조회 중 (" + data.enrich_total + "건)…" : "네이버에서 사업자번호 수집 중…";
          }}
          if (data.status === "done") {{
            document.getElementById("status").innerHTML = "수집 완료: <strong>" + (data.results ? data.results.length : 0) + "</strong>건";
            if (data.filepath && !document.querySelector("#doneArea a[href*='download']")) {{
              var a = document.createElement("a");
              a.href = "/download/" + data.filepath;
              a.className = "btn";
              a.textContent = "엑셀 파일 다운로드";
              document.getElementById("doneArea").appendChild(a);
            }}
            document.getElementById("doneArea").style.display = "block";
            return;
          }}
          if (data.status === "error") {{
            document.getElementById("status").innerHTML = "오류: " + (data.error || "알 수 없음");
            document.getElementById("doneArea").style.display = "block";
            return;
          }}
          setTimeout(poll, 1500);
        }})
        .catch(function() {{ setTimeout(poll, 2000); }});
    }}
    poll();
  </script>
""" + _html_foot()


@app.route("/progress/status/<job_id>")
def progress_status(job_id):
    """수집 진행 상태 JSON (폴링용)."""
    with _jobs_lock:
        job = _jobs.get(job_id, {})
    return jsonify({
        "status": job.get("status", "unknown"),
        "results": job.get("results", []),
        "filepath": job.get("filepath"),
        "enrich_total": job.get("enrich_total"),
        "error": job.get("error"),
    })


@app.route("/download/<filename>")
def download(filename):
    if ".." in filename or "/" in filename or "\\" in filename:
        return "Not found", 404
    base = Path(ROOT) / "data"
    path = base / filename
    if not path.is_file():
        return "Not found", 404
    download_name = path.name
    if path.suffix.lower() == ".xlsx":
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        mimetype = None
    return send_file(path, as_attachment=True, download_name=download_name, mimetype=mimetype)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    def _open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()
    print(f"\n  브라우저에서 열기: {url}\n  (이 창을 닫으면 프로그램이 종료됩니다)\n")
    app.run(host=host, port=port, debug=False, use_reloader=False)
