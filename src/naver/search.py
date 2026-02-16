"""네이버 쇼핑 검색 URL 생성 및 페이지 이동."""
from urllib.parse import urlencode

from config.settings import NAVER_SEARCH_BASE
from src.naver.constants import PAGING_SIZE, SORT_OPTIONS


def build_search_url(
    query: str,
    sort_key: str = "랭킹",
    paging_index: int = 1,
    paging_size: int = PAGING_SIZE,
) -> str:
    """
    네이버 쇼핑 전체 검색 URL 생성.

    :param query: 검색 키워드
    :param sort_key: SORT_OPTIONS 키 (랭킹, 낮은가격, 높은가격, 리뷰많은순, 리뷰좋은순, 등록일순)
    :param paging_index: 페이지 번호 (1부터)
    :param paging_size: 페이지당 상품 수
    """
    sort_value = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["랭킹"])
    params = {
        "query": query,
        "origQuery": query,
        "adQuery": query,
        "frm": "NVSCPRO",
        "pagingIndex": paging_index,
        "pagingSize": paging_size,
        "productSet": "total",
        "sort": sort_value,
        "viewType": "list",
    }
    return f"{NAVER_SEARCH_BASE}?{urlencode(params)}"


def get_sort_display_name(sort_key: str) -> str:
    """정렬 옵션 한글 표시명."""
    names = {
        "랭킹": "네이버 랭킹순",
        "낮은가격": "낮은 가격순",
        "높은가격": "높은 가격순",
        "리뷰많은순": "리뷰 많은순",
        "리뷰좋은순": "리뷰 좋은순",
        "등록일순": "등록일순",
    }
    return names.get(sort_key, sort_key)
