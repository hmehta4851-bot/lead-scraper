"""One browser process with isolated contexts/pages for each lead source."""
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

_pw = None
_browser: Browser = None
_pages: dict[str, Page] = {}
_contexts: dict[str, BrowserContext] = {}


def get_page(source: str = "shared") -> Page:
    global _pw, _browser
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
    page = _pages.get(source)
    if page is None or page.is_closed():
        old_context = _contexts.get(source)
        if old_context is not None:
            try:
                old_context.close()
            except Exception:
                pass
        context = _browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        _contexts[source] = context
        _pages[source] = page
    return page


def close():
    global _pw, _browser
    for context in list(_contexts.values()):
        try:
            context.close()
        except Exception:
            pass
    _contexts.clear()
    _pages.clear()
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
