"""
Web Search Tool
===============
Performs web searches using DuckDuckGo (no API key required)
or Bing Search API (requires key).
"""

import httpx
import asyncio
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from ..utils.logger import get_logger
from ...config import settings

logger = get_logger(__name__)


class WebSearchTool:
    """
    Search the web and return structured results.
    Primary: DuckDuckGo HTML scraping (no key needed)
    Fallback: Bing Search API (if configured)
    """

    DDGO_URL = "https://html.duckduckgo.com/html/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    async def search(self, query: str, num_results: int = 10) -> dict:
        """
        Search the web for a query.

        Args:
            query: Search query string
            num_results: Number of results to return (max 10)

        Returns:
            dict with results list, each having title, url, snippet
        """
        logger.info(f"Searching: {query[:60]}")
        try:
            results = await self._ddgo_search(query, num_results)
            if results:
                return {"success": True, "query": query, "results": results}
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")

        # Fallback to Bing
        try:
            results = await self._bing_search(query, num_results)
            if results:
                return {"success": True, "query": query, "results": results, "source": "bing"}
        except Exception as e:
            logger.error(f"Bing search also failed: {e}")

        return {"success": False, "query": query, "results": [], "error": "All search backends failed"}

    async def _ddgo_search(self, query: str, n: int) -> list[dict]:
        """Scrape DuckDuckGo HTML results."""
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.post(
                self.DDGO_URL,
                data={"q": query, "b": ""},
                headers=self.HEADERS,
            )
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        results = []

        for result in soup.select(".result__body")[:n]:
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            if not title_el:
                continue
            results.append({
                "title":   title_el.get_text(strip=True),
                "url":     title_el.get("href", ""),
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })

        return results

    async def _bing_search(self, query: str, n: int) -> list[dict]:
        """Use Bing Web Search API."""
        key = getattr(settings, "BING_SEARCH_KEY", None)
        if not key:
            return []

        url = "https://api.bing.microsoft.com/v7.0/search"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                url,
                params={"q": query, "count": n, "mkt": "en-US"},
                headers={"Ocp-Apim-Subscription-Key": key},
            )
            response.raise_for_status()
            data = response.json()

        return [
            {
                "title":   r.get("name", ""),
                "url":     r.get("url", ""),
                "snippet": r.get("snippet", ""),
            }
            for r in data.get("webPages", {}).get("value", [])[:n]
        ]
