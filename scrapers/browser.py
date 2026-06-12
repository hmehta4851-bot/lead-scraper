"""
Shared Playwright browser singleton for all scrapers.
Single browser instance per process — avoids launching multiple browsers.
"""
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

_pw = None
_browser: Browser = None
_page: Page = None
_ctx: BrowserContext = None


def get_page() -> Page:
    global _pw, _browser, _ctx, _page
    if _pw is None:
        _pw = sync_playwright().start()
    if _browser is None or not _browser.is_connected():
        _browser = _pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        _ctx = _browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
        )
        _page = _ctx.new_page()
        _page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    return _page


def close():
    global _pw, _browser, _ctx, _page
    if _browser:
        try:
            _browser.close()
        except Exception:
            pass
        _browser = None
    if _pw:
        try:
            _pw.stop()
        except Exception:
            pass
        _pw = None
    _ctx = None
    _page = None
