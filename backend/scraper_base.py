import asyncio
import logging
from abc import ABC, abstractmethod
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, proxy_url: str = None):
        self.proxy_url = proxy_url
        self.browser = None
        self.playwright = None

    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            browser_args = {}
            if self.proxy_url:
                browser_args["proxy"] = {"server": self.proxy_url}
            self.browser = await self.playwright.chromium.launch(headless=True, **browser_args)
            logger.info("Browser started.")

    async def stop(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        logger.info("Browser stopped.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_page(self, url: str):
        if not self.browser:
            await self.start()

        context = await self.browser.new_context()
        page = await context.new_page()
        # Using stealth_async as specifically requested by user
        await Stealth().apply_stealth_async(page)

        try:
            # Jitter: sleep a random amount between 1 and 3 seconds
            jitter = random.uniform(1.0, 3.0)
            logger.info(f"Jitter: sleeping {jitter:.2f} seconds before fetching")
            await asyncio.sleep(jitter)

            logger.info(f"Fetching URL: {url}")
            # wait_until="domcontentloaded" is generally faster and more reliable than "networkidle"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Additional small sleep to let potential initial JS run
            await asyncio.sleep(2)
            return page, context
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            await page.close()
            await context.close()
            raise e

    @abstractmethod
    async def scrape_url(self, url: str):
        pass
