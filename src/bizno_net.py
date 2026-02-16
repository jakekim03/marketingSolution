"""bizno.net 기업 상세 페이지에서 회사이름·회사이메일 추출."""
import time
from typing import Optional, Tuple

from playwright.sync_api import Page

BIZNO_ARTICLE_URL = "https://bizno.net/article/"


def scrape_company_info(page: Page, bizno: str) -> Tuple[Optional[str], Optional[str]]:
    """
    https://bizno.net/article/{bizno} 페이지를 열고
    맨 위 회사이름, 표의 회사이메일 주소를 추출해 (회사이름, 회사이메일) 반환.
    """
    url = f"{BIZNO_ARTICLE_URL}{bizno}"
    company_name: Optional[str] = None
    company_email: Optional[str] = None

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(1.2)

        # 회사이름: 페이지 상단 제목 (h1 또는 첫 번째 큰 제목)
        for sel in ["h1", "[class*='article'] h1", "[class*='title']", "h2"]:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    text = loc.inner_text().strip()
                    if text and len(text) < 200 and "회사이메일" not in text:
                        company_name = text
                        break
            except Exception:
                continue
        if not company_name:
            try:
                loc = page.locator("h1")
                if loc.count() > 0:
                    company_name = loc.first.inner_text().strip() or None
            except Exception:
                pass

        # 회사이메일: 표에서 '회사이메일' 행의 값 셀 (레이블 옆 셀)
        try:
            row = page.locator("tr:has-text('회사이메일')").first
            if row.count() > 0:
                for sel in ["td", "th"]:
                    cells = row.locator(sel)
                    for i in range(cells.count()):
                        t = cells.nth(i).inner_text().strip()
                        if t and "@" in t and "회사이메일" not in t:
                            company_email = t
                            break
                    if company_email:
                        break
            if not company_email:
                body = page.locator("body").inner_text()
                for line in body.splitlines():
                    line = line.strip()
                    if "회사이메일" in line and "@" in line:
                        for part in line.replace("회사이메일", " ").split():
                            if "@" in part:
                                company_email = part.strip(":,.")
                                break
                        if company_email:
                            break
        except Exception:
            pass

        return (company_name or None, company_email or None)
    except Exception:
        return (None, None)
