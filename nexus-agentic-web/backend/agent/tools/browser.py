"""
Browser Tool
============
Playwright-based browser automation tool for the NEXUS agent.
Handles navigation, interaction, screenshot capture, and DOM parsing.
"""

import base64
import asyncio
from typing import Optional
from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page,
    PlaywrightContextManager, TimeoutError as PlaywrightTimeout
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BrowserTool:
    """
    Wraps Playwright for headless browser automation.
    Manages a single browser instance with persistent context.
    """

    def __init__(self):
        self._playwright: Optional[PlaywrightContextManager] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Lazily initialize browser on first use."""
        if self._initialized:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self._page = await self._context.new_page()

        # Block ads and trackers to speed things up
        await self._context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico}", lambda route: route.abort())
        await self._context.route("**/analytics**", lambda route: route.abort())
        await self._context.route("**/ads/**", lambda route: route.abort())

        self._initialized = True
        logger.info("Browser initialized")

    async def navigate(self, url: str, wait_for: str = "domcontentloaded") -> dict:
        """
        Navigate to a URL and return page metadata + text content.

        Args:
            url: URL to navigate to
            wait_for: Playwright wait_until option

        Returns:
            dict with url, title, text_content, html_snippet
        """
        await self._ensure_initialized()

        try:
            response = await self._page.goto(
                url,
                wait_until=wait_for,
                timeout=15000
            )

            # Wait a bit for JS to render
            await asyncio.sleep(1)

            title = await self._page.title()
            current_url = self._page.url

            # Extract visible text (truncated)
            text_content = await self._page.evaluate("""() => {
                const elements = document.querySelectorAll('p, h1, h2, h3, h4, li, td, th, span[class*="price"], div[class*="result"]');
                return Array.from(elements)
                    .map(el => el.innerText.trim())
                    .filter(t => t.length > 10)
                    .slice(0, 80)
                    .join('\\n');
            }""")

            # Extract links (top 20)
            links = await self._page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({text: a.innerText.trim(), href: a.href}))
                    .filter(l => l.text && l.href.startsWith('http'))
                    .slice(0, 20);
            }""")

            status = response.status if response else 0
            logger.info(f"Navigated to {url} (HTTP {status})")

            return {
                "success": True,
                "url": current_url,
                "title": title,
                "status_code": status,
                "text_content": text_content[:3000],
                "links": links,
            }

        except PlaywrightTimeout:
            logger.warning(f"Timeout navigating to {url}")
            return {"success": False, "url": url, "error": "Page load timeout (15s)"}

        except Exception as e:
            logger.error(f"Navigation error for {url}: {e}")
            return {"success": False, "url": url, "error": str(e)}

    async def click(self, selector: str = None, text: str = None) -> dict:
        """Click an element by CSS selector or text content."""
        await self._ensure_initialized()
        try:
            if selector:
                await self._page.click(selector, timeout=5000)
            elif text:
                await self._page.get_by_text(text).first.click(timeout=5000)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fill_input(self, selector: str, value: str) -> dict:
        """Fill a form input field."""
        await self._ensure_initialized()
        try:
            await self._page.fill(selector, value)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(self) -> dict:
        """Capture a screenshot of the current page."""
        await self._ensure_initialized()
        try:
            data = await self._page.screenshot(
                type="jpeg",
                quality=60,
                clip={"x": 0, "y": 0, "width": 1280, "height": 600},
            )
            b64 = base64.b64encode(data).decode()
            return {"success": True, "screenshot_b64": b64, "format": "jpeg"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def scroll(self, direction: str = "down", amount: int = 500) -> dict:
        """Scroll the page."""
        await self._ensure_initialized()
        try:
            delta = amount if direction == "down" else -amount
            await self._page.evaluate(f"window.scrollBy(0, {delta})")
            await asyncio.sleep(0.5)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_current_url(self) -> str:
        """Return the current page URL."""
        if self._page:
            return self._page.url
        return ""

    async def close(self):
        """Shut down browser cleanly."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning(f"Browser cleanup warning: {e}")
        finally:
            self._initialized = False
