"""
Form Filler Tool
================
Fills and submits web forms intelligently.
Uses LLM to map user-provided field data to form inputs.
"""

import asyncio
from typing import Optional
from ...utils.logger import get_logger

logger = get_logger(__name__)


class FormFillerTool:
    """
    Fills web forms by matching provided data to form fields.
    Handles text inputs, dropdowns, checkboxes, and file uploads.
    """

    def __init__(self):
        self._browser = None  # Injected by agent core

    def set_browser(self, browser):
        """Inject browser dependency."""
        self._browser = browser

    async def fill(
        self,
        fields: dict,
        submit: bool = False,
        submit_selector: Optional[str] = None,
    ) -> dict:
        """
        Fill a web form with provided field values.

        Args:
            fields: Dict mapping field selectors/names to values
                    e.g., {"#email": "user@example.com", "#name": "John"}
            submit: Whether to submit the form after filling
            submit_selector: CSS selector for submit button

        Returns:
            dict with success status and filled field count
        """
        if not self._browser or not self._browser._page:
            return {"success": False, "error": "Browser not initialized"}

        page = self._browser._page
        filled = []
        errors = []

        for selector, value in fields.items():
            try:
                # Determine field type
                field_type = await page.evaluate(
                    f"""() => {{
                        const el = document.querySelector('{selector}');
                        return el ? el.tagName.toLowerCase() + ':' + (el.type || '') : 'notfound';
                    }}"""
                )

                if field_type == "notfound":
                    # Try by name attribute
                    alt_selector = f'[name="{selector}"]'
                    field_type = await page.evaluate(
                        f"""() => {{
                            const el = document.querySelector('{alt_selector}');
                            return el ? el.tagName.toLowerCase() + ':' + (el.type || '') : 'notfound';
                        }}"""
                    )
                    if field_type != "notfound":
                        selector = alt_selector

                if "select" in field_type:
                    await page.select_option(selector, str(value))
                elif "input:checkbox" in field_type or "input:radio" in field_type:
                    if value:
                        await page.check(selector)
                    else:
                        await page.uncheck(selector)
                elif "input:file" in field_type:
                    # File upload — value should be a local path
                    await page.set_input_files(selector, str(value))
                else:
                    await page.fill(selector, str(value))

                filled.append(selector)
                await asyncio.sleep(0.1)  # Small delay between fields

            except Exception as e:
                logger.warning(f"Failed to fill {selector}: {e}")
                errors.append({"selector": selector, "error": str(e)})

        result = {
            "success": len(filled) > 0,
            "filled_count": len(filled),
            "filled": filled,
            "errors": errors,
        }

        # Submit form if requested
        if submit and len(filled) > 0:
            try:
                if submit_selector:
                    await page.click(submit_selector)
                else:
                    # Try common submit patterns
                    for sel in ['[type="submit"]', 'button[type="submit"]', '.submit-btn', '#submit']:
                        try:
                            await page.click(sel, timeout=2000)
                            result["submitted"] = True
                            break
                        except Exception:
                            continue

                await asyncio.sleep(1)  # Wait for navigation
                result["current_url"] = page.url

            except Exception as e:
                result["submit_error"] = str(e)

        return result
