"""네이버 쇼핑 검색 상수 (정렬 등)."""
from typing import Dict

# 정렬 옵션 → URL sort 파라미터 (실제 값은 네이버 페이지에서 확인 후 수정)
SORT_OPTIONS: Dict[str, str] = {
    "랭킹": "rel",           # 네이버 랭킹순
    "낮은가격": "prc_asc",   # 낮은 가격순
    "높은가격": "prc_desc",  # 높은 가격순
    "리뷰많은순": "review",  # 리뷰 많은순 (사용자 URL 기준)
    "리뷰좋은순": "review_asc",
    "등록일순": "date",
}

# 검색 결과 페이지당 상품 수 (네이버 기본 40)
PAGING_SIZE = 40

# 검색 결과 리스트 컨테이너 (캡쳐한 구조 기준)
# #content > div.style_content__AlF53 > div.basicList_list_basis__XVx_G
SELECTOR_LIST_CONTAINER = "div[class*='basicList_list_basis']"
# 컨테이너 안의 상품 div 개수만큼 돌림 (wrapper 안에 adProduct_item, superSavingProduct_item, product_item 등)
SELECTOR_LIST_ITEM = "div[class*='basicList_list_basis'] div[class*='_item']"

# 위 셀렉터가 안 먹을 때 시도할 폴백
SELECTOR_PRODUCT_ITEMS = [
    "li[class*='basicList_item']",
    "li[class*='product_item']",
    "div[class*='product_list'] > ul > li",
    "ul[class*='list_basis'] > li",
]

# 정보 버튼 / 레이어 셀렉터 (클래스명 변경 시 여기만 수정)
SELECTOR_BTN_INFO = "button.common_btn_detail__clSR7"
SELECTOR_LAYER_DESC = "div.layer_desc__Juas1"
# 레이어 내 업체명 (없으면 "-" 표시, 실제 셀렉터는 페이지에서 확인 후 수정)
SELECTOR_LAYER_COMPANY = ["div[class*='layer'][class*='title']", "div[class*='layer'] span", ".layer_title"]
# 레이어 닫기(X) 버튼 - 클릭해서 닫아야 아래 정보 버튼이 가리지 않음 (순서대로 시도)
SELECTOR_LAYER_CLOSE = [
    "button[class*='layer_close']",
    "button[class*='close']",
    "[class*='layer'] button[aria-label='닫기']",
    "[class*='layer'] button[title='닫기']",
    ".layer_header button",
]
