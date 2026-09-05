import time
from typing import Callable, Optional, Dict
from contextlib import contextmanager
from typing import Generator
from playwright.sync_api import sync_playwright, Page, BrowserContext


def get_html(
    url: str,
    wait_time: int = 3,
    referer_url: Optional[str] = None,
    action_callback: Optional[Callable[[Page], None]] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    headless: bool = False,
) -> str:
    """
    Generic utility function to fetch fully rendered HTML across multiple websites.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--start-maximized",
                "--disable-features=Translate",
            ],
        )

        headers = custom_headers or {}
        if referer_url:
            headers["Referer"] = referer_url

        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            extra_http_headers=headers,
        )

        page = context.new_page()

        try:
            if referer_url:
                page.goto(referer_url, wait_until="domcontentloaded")
                time.sleep(1)

            page.goto(url, wait_until="networkidle")
            time.sleep(wait_time)

            if action_callback:
                action_callback(page)
                time.sleep(wait_time)

            return page.content()

        except Exception as e:
            print(f"[get_html Error] Failed to process {url}: {e}")
            raise e

        finally:
            browser.close()
