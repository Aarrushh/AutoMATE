import asyncio
import json
import logging
import random
import re
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

# Constants
BASE_URLS = [
    "https://www.make.com/en/templates",
    "https://www.make.com/en/integrations"
]
OUTPUT_FILE = "data/automations_library.json"
ERROR_LOG_FILE = "error_log.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

class MakeScraper:
    def __init__(self):
        self.items = []
        self.seen_urls = set()
        self.total_scraped = 0
        self.load_existing()

    def load_existing(self):
        try:
            with open(OUTPUT_FILE, "r") as f:
                content = json.load(f)
                self.items = content.get("data", [])
                self.seen_urls = {item["url"] for item in self.items}
                self.total_scraped = len(self.items)
                logger.info(f"Loaded {self.total_scraped} existing items.")
        except:
            pass

    def log_error(self, message):
        timestamp = datetime.now().isoformat()
        with open(ERROR_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
        logger.error(message)

    async def scrape_url(self, page, url):
        """Scrapes a single Make template URL."""
        try:
            logger.info(f"Scrating Make URL: {url}")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            if response and response.status >= 400:
                logger.error(f"Make URL {url} returned status {response.status}")
                return None

            # Try to extract __NEXT_DATA__
            next_data_el = await page.query_selector("script#__NEXT_DATA__")
            if next_data_el:
                content = await next_data_el.inner_text()
                data = json.loads(content)
                # Structure might vary, this is a heuristic based on common __NEXT_DATA__
                template_data = data.get("props", {}).get("pageProps", {}).get("template", {})

                if template_data:
                    apps = template_data.get("apps", [])
                    trigger_app = apps[0].get("name") if apps else "Unknown"
                    action_apps = [a.get("name") for a in apps[1:]] if len(apps) > 1 else ["Unknown Action"]

                    return {
                        "name": template_data.get("name") or "Unknown Make Template",
                        "description": template_data.get("description") or "",
                        "url": url,
                        "source_platform": "Make",
                        "trigger_app": trigger_app,
                        "action_apps": action_apps,
                        "raw_data": template_data
                    }

            # Fallback
            title_el = await page.query_selector("h1")
            title = await title_el.inner_text() if title_el else "Unknown Make Template"

            # Extract tools from images if possible
            tools = []
            tool_imgs = await page.query_selector_all("img")
            for img in tool_imgs:
                alt = await img.get_attribute("alt")
                if alt and "logo" in alt.lower():
                    tools.append(alt.replace(" logo", ""))

            return {
                "name": title.strip(),
                "description": title.strip(),
                "url": url,
                "source_platform": "Make",
                "trigger_app": tools[0] if tools else "Unknown",
                "action_apps": tools[1:] if len(tools) > 1 else ["Unknown Action"],
                "raw_data": {"url": url}
            }
        except Exception as e:
            self.log_error(f"Error scraping Make URL {url}: {e}")
            return None

    async def scrape(self, urls=None):
        target_urls = urls if urls else BASE_URLS
        async with async_playwright() as p:
            logger.info("Launching browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            try:
                for base_url in target_urls:
                    await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(5)
                    await self.scrape_category(page, base_url)
            except Exception as e:
                self.log_error(f"Scraper encountered a critical error: {str(e)}")
            finally:
                await browser.close()
                self.save_data()

    async def scrape_category(self, page, category_url):
        last_height = await page.evaluate("document.body.scrollHeight")
        while self.total_scraped < 5000:
            await self.extract_items_from_page(page)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2.5)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height: break
            last_height = new_height

    async def extract_items_from_page(self, page):
        cards = await page.query_selector_all(".template-card, .integration-item")
        for card in cards:
            if self.total_scraped >= 5000: break
            try:
                url_el = await card.query_selector("a")
                url = await url_el.get_attribute("href") if url_el else None
                if not url: continue
                full_url = url if url.startswith("http") else f"https://www.make.com{url}"
                if full_url in self.seen_urls: continue

                name_el = await card.query_selector(".template-title")
                name = await name_el.inner_text() if name_el else "Unknown Template"

                tools = []
                tool_imgs = await card.query_selector_all("img")
                for img in tool_imgs:
                    alt = await img.get_attribute("alt")
                    if alt: tools.append(alt)

                item = {
                    "name": name.strip(),
                    "description": "",
                    "url": full_url,
                    "tools": list(set(tools))
                }
                self.items.append(item)
                self.seen_urls.add(full_url)
                self.total_scraped += 1
            except: continue
        self.save_data()

    def save_data(self):
        data = {"total_count": len(self.items), "data": self.items}
        try:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except: pass

if __name__ == "__main__":
    scraper = MakeScraper()
    asyncio.run(scraper.scrape())
