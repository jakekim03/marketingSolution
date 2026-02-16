"""네이버 쇼핑 검색 결과에서 '정보' 버튼 클릭 후 사업자등록번호 수집 (중복 제외)."""
import re
import time
from typing import Callable, List, Optional, Set

from playwright.sync_api import Page

from src.naver.constants import (
    SELECTOR_BTN_INFO,
    SELECTOR_LAYER_DESC,
    SELECTOR_LAYER_COMPANY,
    SELECTOR_LAYER_CLOSE,
    SELECTOR_LIST_CONTAINER,
    SELECTOR_LIST_ITEM,
    SELECTOR_PRODUCT_ITEMS,
)
from src.naver.search import build_search_url
from src.naver.login import wait_for_manual_login


def _normalize_bizno(text: Optional[str]) -> Optional[str]:
    """텍스트에서 숫자만 추출. 10자리면 사업자등록번호로 인정."""
    if not text or not text.strip():
        return None
    digits = re.sub(r"\D", "", text.strip())
    if not digits:
        return None
    # 사업자등록번호는 10자리 (하이픈 제외)
    return digits if len(digits) == 10 else None


def extract_info_value_from_layer(page: Page) -> Optional[str]:
    """
    정보 버튼 클릭 후 뜬 레이어에서 div.layer_desc__Juas1 중
    **10자리 숫자(사업자등록번호)** 인 값만 반환. 다른 값(통신판매업번호 등)은 제외.
    """
    try:
        loc = page.locator(SELECTOR_LAYER_DESC)
        n = loc.count()
        if n == 0:
            return None
        # 보이는 것만 검사, 10자리 숫자인 것만 사업자등록번호로 인정
        for idx in range(n - 1, -1, -1):
            el = loc.nth(idx)
            try:
                if not el.is_visible():
                    continue
                text = el.inner_text().strip()
                bizno = _normalize_bizno(text)
                if bizno:  # 10자리일 때만 반환
                    return bizno
            except Exception:
                continue
        return None
    except Exception:
        return None


def extract_company_name_from_layer(page: Page) -> Optional[str]:
    """정보 레이어에서 업체명 추출. 없으면 None (화면에서는 '-' 표시)."""
    for sel in SELECTOR_LAYER_COMPANY:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                for idx in range(loc.count()):
                    el = loc.nth(idx)
                    if el.is_visible():
                        t = el.inner_text().strip()
                        if t and len(t) < 100 and not re.match(r"^\d+$", t):
                            return t
        except Exception:
            continue
    return None


def _get_product_item_selector(page: Page) -> Optional[str]:
    """보이는 상품 리스트가 있는 셀렉터를 찾음. 없으면 None."""
    for sel in SELECTOR_PRODUCT_ITEMS:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                return sel
        except Exception:
            continue
    return None


def _close_layer_by_x(page: Page) -> bool:
    """레이어의 X(닫기) 버튼을 클릭해서 닫기. 성공하면 True, 못 찾으면 False."""
    for sel in SELECTOR_LAYER_CLOSE:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.click(timeout=3000)
                return True
        except Exception:
            continue
    return False


def _collect_one_button(page: Page, btn) -> Optional[str]:
    """정보 버튼 클릭 → 사업자번호 추출 → 레이어 닫기 후 다음으로. 사업자등록번호만 반환."""
    try:
        btn.scroll_into_view_if_needed(timeout=8000)
        time.sleep(0.6)
        btn.click(timeout=8000)
        time.sleep(1.2)
        bizno = extract_info_value_from_layer(page)
        if not _close_layer_by_x(page):
            page.keyboard.press("Escape")
        time.sleep(0.8)
        return bizno
    except Exception:
        try:
            _close_layer_by_x(page)
        except Exception:
            pass
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        time.sleep(0.8)
        return None


def _scroll_to_bottom_and_wait(page: Page) -> None:
    """
    시작 전에 맨 아래까지 스크롤해서 상품 전부 로드.
    업데이트될 때까지 대기한 뒤 수집 시작.
    """
    scroll_step = 700
    max_scrolls = 30
    for _ in range(max_scrolls):
        page.evaluate(f"window.scrollBy(0, {scroll_step})")
        time.sleep(1.0)
        at_bottom = page.evaluate(
            "() => window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 100"
        )
        if at_bottom:
            break
    time.sleep(1.5)  # 마지막 로드까지 반영될 때까지 대기


def get_info_values_on_current_page(
    page: Page,
    on_each: Optional[Callable[[Optional[str]], bool]] = None,
) -> List[Optional[str]]:
    """
    상품 순서대로 정보 버튼 클릭 → 사업자번호 추출 → 레이어 닫고 다음으로.
    on_each(bizno) 호출 후 True 반환하면 즉시 수집 중단 (목표 개수 달성 시).
    """
    values: List[Optional[str]] = []

    try:
        container = page.locator(SELECTOR_LIST_CONTAINER).first
        container.wait_for(state="visible", timeout=5000)
    except Exception:
        container = None

    if container:
        _scroll_to_bottom_and_wait(page)
        count = container.locator("div[class*='_item']").count()
        for i in range(count):
            if on_each and on_each(None):
                break
            try:
                item = container.locator("div[class*='_item']").nth(i)
                item.evaluate("el => el.scrollIntoView({ block: 'center', behavior: 'instant' })")
                time.sleep(0.6)
                buttons_in_item = item.locator(SELECTOR_BTN_INFO)
                btn = None
                for j in range(buttons_in_item.count()):
                    b = buttons_in_item.nth(j)
                    if b.inner_text().strip() == "정보":
                        btn = b
                        break
                if btn is None:
                    values.append(None)
                    continue
                bizno = _collect_one_button(page, btn)
                values.append(bizno)
                if on_each and on_each(bizno):
                    break
            except Exception:
                values.append(None)
                try:
                    _close_layer_by_x(page)
                except Exception:
                    pass
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
                time.sleep(0.8)
        return values

    product_sel = _get_product_item_selector(page)
    if product_sel:
        items = page.locator(product_sel)
        count = items.count()
        for i in range(count):
            if on_each and on_each(None):
                break
            try:
                items = page.locator(product_sel)
                item = items.nth(i)
                item.scroll_into_view_if_needed(timeout=8000)
                time.sleep(0.8)
                buttons_in_item = item.locator(SELECTOR_BTN_INFO)
                btn = None
                for j in range(buttons_in_item.count()):
                    b = buttons_in_item.nth(j)
                    if b.inner_text().strip() == "정보":
                        btn = b
                        break
                if btn is None:
                    values.append(None)
                    continue
                bizno = _collect_one_button(page, btn)
                values.append(bizno)
            except Exception:
                values.append(None)
                try:
                    _close_layer_by_x(page)
                except Exception:
                    pass
                time.sleep(0.5)
        return values

    buttons = page.locator(SELECTOR_BTN_INFO)
    for i in range(buttons.count()):
        if on_each and on_each(None):
            break
        try:
            btn = buttons.nth(i)
            if btn.inner_text().strip() != "정보":
                values.append(None)
                continue
            bizno = _collect_one_button(page, btn)
            values.append(bizno)
            if on_each and on_each(bizno):
                break
        except Exception:
            values.append(None)
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            time.sleep(0.5)

    return values


def scrape_search_results(
    page: Page,
    query: str,
    sort_key: str = "랭킹",
    max_count: int = 50,
    *,
    already_logged_in: bool = False,
    already_on_first_page: bool = False,
    on_item: Optional[Callable[[str], None]] = None,
) -> List[str]:
    """
    중복 제외하고 고유 사업자등록번호 max_count개만 수집. 페이지는 필요 시 자동으로 넘김.
    on_item(bizno)는 새로 추가된 고유 번호마다만 호출 (실시간 저장·화면 표시용).
    """
    if not already_logged_in:
        wait_for_manual_login(page)

    seen: Set[str] = set()
    all_values: List[str] = []
    paging_index = 1

    while len(all_values) < max_count:
        if paging_index == 1 and already_on_first_page:
            time.sleep(1.0)
        else:
            url = build_search_url(query=query, sort_key=sort_key, paging_index=paging_index)
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.locator(SELECTOR_LIST_CONTAINER).first.wait_for(state="visible", timeout=30000)
            except Exception:
                page.locator(SELECTOR_BTN_INFO).first.wait_for(state="visible", timeout=15000)
            time.sleep(1.0)

        def _on_each(b: Optional[str]) -> bool:
            if b and b not in seen:
                seen.add(b)
                all_values.append(b)
                if on_item:
                    on_item(b)
            return len(all_values) >= max_count

        page_values = get_info_values_on_current_page(page, on_each=_on_each)
        if len(page_values) == 0:
            break
        if len(all_values) >= max_count:
            break
        paging_index += 1
        time.sleep(0.8)

    return all_values
