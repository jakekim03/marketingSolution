"""네이버 로그인 (수동 로그인 대기)."""
from playwright.sync_api import Page


def wait_for_manual_login(page: Page, login_url: str = "https://nid.naver.com/nidlogin.login") -> None:
    """
    네이버 로그인 페이지를 열고, 사용자가 직접 로그인할 때까지 대기합니다.
    로그인을 완료한 후 터미널에서 Enter를 누르면 다음 단계로 진행합니다.

    :param page: Playwright Page
    :param login_url: 로그인 페이지 URL
    """
    page.goto(login_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=15000)
    print("\n[수동 로그인] 브라우저에서 네이버 로그인을 완료한 뒤, 여기로 돌아와서 Enter 키를 누르세요.")
    input()
