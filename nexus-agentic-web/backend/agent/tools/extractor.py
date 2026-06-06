"""
Data Extractor Tool
===================
Uses LLM to extract structured data from raw HTML/text.
Supports custom schemas, tables, lists, and key-value pairs.
"""

import json
import re
from typing import Any, Optional
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from ...config import settings
from ...utils.logger import get_logger

logger = get_logger(__name__)

EXTRACT_SYSTEM = """You are a data extraction specialist. Extract structured data from the given text according to the requested schema.

Rules:
- Return ONLY valid JSON, nothing else
- If a field is missing, use null
- For lists, extract all instances
- Be precise — copy exact values (prices, names, dates) from the source
- Confidence: add a "_confidence" field (0.0–1.0) per extracted object

Return format: {"data": [...extracted items...], "count": N, "confidence": 0.0-1.0}"""


class DataExtractorTool:
    """
    LLM-powered data extraction from web page content.
    Converts unstructured HTML/text into structured JSON.
    """

    def __init__(self):
        self.llm = self._init_llm()

    def _init_llm(self):
        try:
            return AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_VERSION,
                temperature=0,
                max_tokens=1500,
            )
        except Exception:
            return ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY, temperature=0)

    async def extract(
        self,
        content: str,
        schema: str,
        context: Optional[str] = None,
    ) -> dict:
        """
        Extract structured data from text using LLM.

        Args:
            content: Raw text/HTML content to extract from
            schema: Description of what to extract (e.g., "company name, funding amount, investors")
            context: Optional context about the page/task

        Returns:
            dict with extracted data
        """
        # Truncate content to avoid token limits
        truncated = content[:4000] if len(content) > 4000 else content

        prompt = f"""Extract the following from this text: {schema}

{"Context: " + context if context else ""}

TEXT TO EXTRACT FROM:
{truncated}
"""
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=EXTRACT_SYSTEM),
                HumanMessage(content=prompt),
            ])

            raw = response.content.strip()
            # Strip markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            parsed = json.loads(raw)
            logger.info(f"Extracted {parsed.get('count', '?')} items with confidence {parsed.get('confidence', '?')}")
            return {"success": True, **parsed}

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in extractor: {e}")
            return {"success": False, "error": "Failed to parse LLM extraction output", "raw": response.content[:200]}

        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return {"success": False, "error": str(e)}

    async def extract_table(self, html: str) -> dict:
        """Extract all tables from HTML as structured data."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        tables = []
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if cells:
                    if headers:
                        rows.append(dict(zip(headers, cells)))
                    else:
                        rows.append(cells)
            if rows:
                tables.append({"headers": headers, "rows": rows})
        return {"success": True, "tables": tables, "count": len(tables)}
