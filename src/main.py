"""
법인 영업용 솔루션 메인: 네이버 쇼핑 검색 → 정보값 수집 → 비즈노 사업자 조회.
"""
import csv
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

from config.settings import BIZNO_API_KEY, HEADLESS, MAX_PAGES_DEFAULT
from src.naver.constants import SORT_OPTIONS
from src.naver.scraper import scrape_search_results
from src.naver.search import get_sort_display_name
from src.bizno.api import lookup_batch


def run(
    keyword: str,
    sort_key: str = "랭킹",
    max_pages: int = 1,
    headless: bool = False,
    output_csv: Optional[str] = None,
    skip_bizno: bool = False,
):
    """
    :param keyword: 검색 키워드 (예: 마스크팩)
    :param sort_key: 정렬 키 (랭킹, 낮은가격, 높은가격, 리뷰많은순, 리뷰좋은순, 등록일순)
    :param max_pages: 수집할 페이지 수
    :param headless: True면 브라우저 숨김
    :param output_csv: 결과 저장 CSV 경로 (None이면 data/result_{keyword}.csv)
    :param skip_bizno: True면 비즈노 조회 생략
    """
    sort_key = sort_key if sort_key in SORT_OPTIONS else "랭킹"
    headless = headless or HEADLESS

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            locale="ko-KR",
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        try:
            print(f"키워드: {keyword}, 정렬: {get_sort_display_name(sort_key)}, 페이지: {max_pages}")
            info_values = scrape_search_results(
                page,
                query=keyword,
                sort_key=sort_key,
                max_pages=max_pages,
                already_logged_in=False,
            )
        finally:
            browser.close()

    # 중복 제거·None 제거 후 사업자등록번호로 간주
    bizno_list = list(dict.fromkeys(v for v in info_values if v))

    print(f"수집된 정보값(사업자번호) 건수: {len(bizno_list)}")

    rows = []
    if not skip_bizno and BIZNO_API_KEY:
        print("비즈노 API로 사업자 정보 조회 중...")
        biz_infos = lookup_batch(bizno_list)
        for bizno, info in zip(bizno_list, biz_infos):
            rows.append({"사업자등록번호": bizno, **info})
    else:
        if skip_bizno:
            print("비즈노 조회 생략 (--skip-bizno)")
        else:
            print("BIZNO_API_KEY 미설정으로 비즈노 조회 생략")
        for bizno in bizno_list:
            rows.append({"사업자등록번호": bizno})

    if not rows:
        print("저장할 결과 없음.")
        return

    out_path = output_csv or Path(__file__).resolve().parent.parent / "data" / f"result_{keyword}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if rows:
        keys = list(rows[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    print(f"저장: {out_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="네이버 쇼핑 검색 → 정보 수집 → 비즈노 사업자 조회")
    parser.add_argument("keyword", help="검색 키워드 (예: 마스크팩)")
    parser.add_argument(
        "--sort",
        choices=list(SORT_OPTIONS.keys()),
        default="랭킹",
        help="정렬 옵션",
    )
    parser.add_argument("--pages", type=int, default=MAX_PAGES_DEFAULT, help="수집할 페이지 수 (기본 1)")
    parser.add_argument("--headless", action="store_true", help="브라우저 숨김 실행")
    parser.add_argument("--output", "-o", help="결과 CSV 경로")
    parser.add_argument("--skip-bizno", action="store_true", help="비즈노 API 조회 생략")
    args = parser.parse_args()

    run(
        keyword=args.keyword,
        sort_key=args.sort,
        max_pages=args.pages,
        headless=args.headless,
        output_csv=args.output,
        skip_bizno=args.skip_bizno,
    )


if __name__ == "__main__":
    main()
