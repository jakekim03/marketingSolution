"""
비즈노 사업자정보 조회 API 클라이언트.
문서: https://bizno.net/openapi
무료: https://api.bizno.net/ (1일 200건, 사업자등록번호|상호명|사업자상태|과세유형)
"""
from typing import Any, Dict, List, Optional

import requests

from config.settings import BIZNO_API_KEY


# 실제 엔드포인트는 비즈노 개발자 문서 확인 후 수정
BIZNO_API_BASE = "https://api.bizno.net"


def lookup_by_bizno(
    bizno: str,
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    사업자등록번호로 사업자 정보 조회 (무료 API 기준).

    :param bizno: 사업자등록번호 (10자리, 하이픈 유무 무관)
    :param api_key: API 키 (미입력 시 BIZNO_API_KEY 환경변수)
    :return: 사업자 정보 딕셔너리 또는 실패 시 None
    """
    api_key = api_key or BIZNO_API_KEY
    if not api_key:
        raise ValueError("BIZNO_API_KEY를 .env에 설정하거나 api_key 인자로 전달하세요.")

    # 숫자만 추출 (10자리)
    bizno_clean = "".join(c for c in bizno if c.isdigit())
    if len(bizno_clean) != 10:
        return None

    # 비즈노 실제 API 스펙에 맞게 수정 필요 (예: GET /search?key=...&bizno=...)
    url = f"{BIZNO_API_BASE}/search"
    params = {"key": api_key, "bizno": bizno_clean}
    headers = {"Accept": "application/json"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # 응답 구조에 따라 필드 매핑 (무료: 사업자등록번호|상호명|사업자상태|과세유형)
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return None
    except requests.RequestException:
        return None
    except Exception:
        return None


def lookup_batch(
    bizno_list: List[str],
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    사업자등록번호 목록으로 일괄 조회 (유료 API에서 일괄조회 지원).
    무료 API면 한 건씩 호출 (1일 200건 제한 주의).

    :param bizno_list: 사업자등록번호 리스트
    :param api_key: API 키
    :return: 조회 결과 리스트 (순서 대응, 실패 건은 None 또는 빈 dict)
    """
    api_key = api_key or BIZNO_API_KEY
    results: List[Dict[str, Any]] = []
    for bizno in bizno_list:
        if not bizno or not str(bizno).strip():
            results.append({})
            continue
        info = lookup_by_bizno(str(bizno).strip(), api_key=api_key)
        results.append(info or {})
    return results
