import abc
import asyncio
import logging
import random
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

class BaseScraper(abc.ABC):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.results = []

    async def init_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080}
        )
        logger.info("Browser initialized.")

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser and Playwright stopped.")

    @abc.abstractmethod
    async def scrape(self):
        """Implement the scraping logic in the subclass."""
        pass

    async def safe_goto(self, page: Page, url: str, retries: int = 3):
        for attempt in range(retries):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                return True
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to load {url} after {retries} attempts.")
                    return False
                await asyncio.sleep(2 ** attempt)
