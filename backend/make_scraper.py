import asyncio
import json
import logging
import random
import re
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BASE_URLS = [
    "https://www.make.com/en/templates",
    "https://www.make.com/en/integrations"
]
OUTPUT_FILE = "data/automations_library.json"
ERROR_LOG_FILE = "error_log.txt"
USER_AGENT = "Mozilla/5.0 (Compatible; AutomationResearchBot/1.0)"

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
        except FileNotFoundError:
            logger.info("No existing data found. Starting fresh.")
        except json.JSONDecodeError:
            logger.error("Failed to decode existing JSON. Starting fresh.")

    def log_error(self, message):
        timestamp = datetime.now().isoformat()
        with open(ERROR_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
        logger.error(message)

    async def scrape(self, urls=None):
        target_urls = urls if urls else BASE_URLS
        async with async_playwright() as p:
            logger.info("Launching browser...")
            browser = await p.chromium.launch(headless=True) # Stealth works better with headless=False usually but we are in a headless env.
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York"
            )
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            try:
                for base_url in target_urls:
                    if self.total_scraped >= 5000:
                        break

                    logger.info(f"Navigating to {base_url}")
                    try:
                        await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
                        await asyncio.sleep(5)  # Wait for initial load

                        await self.scrape_category(page, base_url)

                    except Exception as e:
                        self.log_error(f"Error accessing {base_url}: {e}")

            except Exception as e:
                self.log_error(f"Scraper encountered a critical error: {str(e)}")
            finally:
                await browser.close()
                self.save_data()

    async def scrape_category(self, page, category_url):
        # We need to scroll and extract until we reach volume or end of page
        last_height = await page.evaluate("document.body.scrollHeight")
        retries = 0
        consecutive_no_new_items = 0

        while self.total_scraped < 5000:
            count_before = self.total_scraped
            await self.extract_items_from_page(page)
            count_after = self.total_scraped

            if count_after == count_before:
                consecutive_no_new_items += 1
            else:
                consecutive_no_new_items = 0

            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2.5) # Wait for content to load (rate limit 1 req/2s constraint respected by waiting > 2s)

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                retries += 1
                if retries > 3:
                    logger.info("Reached bottom of page or infinite scroll limit.")
                    break
            else:
                retries = 0
            last_height = new_height

            if consecutive_no_new_items > 5:
                logger.info("No new items found in last 5 scrolls. Stopping category.")
                break

    async def extract_items_from_page(self, page):
        # Selectors
        # container: .template-card, .integration-item
        cards = await page.query_selector_all(".template-card, .integration-item")

        new_items_count = 0
        for card in cards:
            if self.total_scraped >= 5000:
                break

            try:
                # Extract URL
                url_el = await card.query_selector("a.template-link")
                if not url_el:
                    # Maybe the card itself is the link or uses a different class for integrations
                    url_el = await card.query_selector("a")

                url = await url_el.get_attribute("href") if url_el else None
                if not url:
                    continue

                full_url = url if url.startswith("http") else f"https://www.make.com{url}"

                if full_url in self.seen_urls:
                    continue

                # Extract Name
                name_el = await card.query_selector(".template-title")
                name = await name_el.inner_text() if name_el else "Unknown Template"

                # Extract Description
                desc_el = await card.query_selector(".template-description")
                description = await desc_el.inner_text() if desc_el else ""

                # Extract Category/Tags
                category_el = await card.query_selector(".template-tags, .category-label")
                category = await category_el.inner_text() if category_el else "Uncategorized"

                # Extract Tools (icons or tags)
                # Heuristic: look for img tags with alt text or title
                tools = []
                tool_imgs = await card.query_selector_all("img")
                for img in tool_imgs:
                    alt = await img.get_attribute("alt")
                    if alt:
                        tools.append(alt)

                # Deduplicate tools
                tools = list(set(tools))

                # Financials & Complexity
                module_count = len(tools)
                if module_count == 0:
                     module_count = 1 # Minimum 1

                # Cost Calculation
                # Cost per 10k ops = 9.00
                # Ops per run = module_count * 1
                ops_per_run = module_count
                cost_per_run = (ops_per_run / 10000.0) * 9.00
                monthly_cost = cost_per_run * 100.0

                # Type Classification
                if len(tools) > 1:
                    type_class = "Multi-product solution"
                elif len(tools) == 1:
                    type_class = "Single-point automation"
                else:
                    type_class = "Workflow automation" # Default if 0 tools found

                # Complexity Tier
                if len(tools) < 3:
                    complexity = "Low"
                elif len(tools) <= 5:
                    complexity = "Mid"
                else:
                    complexity = "High"

                item = {
                    "name": name.strip(),
                    "description": description.strip(),
                    "category": category.strip(),
                    "type": type_class,
                    "tools": tools,
                    "url": full_url,
                    "financials": {
                        "setup_cost": "Free (Template)",
                        "estimated_operating_cost_per_month": round(monthly_cost, 6), # More precision
                        "complexity_tier": complexity
                    }
                }

                self.items.append(item)
                self.seen_urls.add(full_url)
                self.total_scraped += 1
                new_items_count += 1

            except Exception as e:
                 # Skip failed item
                 # self.log_error(f"Failed to extract item: {e}")
                 continue

        if new_items_count > 0:
            logger.info(f"Scraped {new_items_count} new items. Total: {self.total_scraped}")
            self.save_data()

    def save_data(self):
        data = {
            "total_count": len(self.items),
            "scrape_date": datetime.now().isoformat(),
            "source": "make.com",
            "data": self.items
        }
        try:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.log_error(f"Failed to save JSON: {e}")

if __name__ == "__main__":
    scraper = MakeScraper()
    asyncio.run(scraper.scrape())
    print(f"Scraped {scraper.total_scraped} items from Make.com successfully")
