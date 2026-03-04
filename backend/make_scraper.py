import asyncio
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class MakeScraper:
    async def scrape_url(self, url: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Use stealth-like context
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle")

                title_el = await page.query_selector('h1[data-test-id="template-name"]')
                title = await title_el.inner_text() if title_el else "Unknown Make Template"

                desc_el = await page.query_selector('[data-test-id="template-description"]')
                description = await desc_el.inner_text() if desc_el else title

                # Extract apps from module icons/labels
                modules = await page.query_selector_all('[data-test-id="module"]')
                raw_apps = []
                for mod in modules:
                    app_name = await mod.get_attribute("data-app-name") or await mod.inner_text()
                    if app_name:
                        raw_apps.append(app_name.strip())

                if not raw_apps:
                    # Fallback extraction from text
                    raw_apps = ["Unknown App"]

                return {
                    "title": title.strip(),
                    "description": description.strip(),
                    "raw_apps": raw_apps,
                    "source": "make"
                }
            finally:
                await browser.close()
