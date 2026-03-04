import asyncio
import random
import logging
from typing import List, Optional, Union
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response
from playwright_stealth import Stealth
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScrapingBlockError(Exception):
    """Exception raised when bot detection is suspected."""
    pass

class BaseScraper:
    """
    A robust base class for web scraping using Playwright.
    Includes stealth, per-context proxy rotation, and intelligent retry logic.
    """

    def __init__(self, proxies: Optional[Union[str, List[str]]] = None, headless: bool = True):
        """
        Initialize the scraper with optional proxies and headless mode.

        :param proxies: A single proxy URL or a list of proxy URLs.
        :param headless: Whether to run the browser in headless mode.
        """
        if isinstance(proxies, str):
            self.proxies = [proxies]
        elif isinstance(proxies, list):
            self.proxies = proxies
        else:
            self.proxies = []

        self.headless = headless
        self.playwright = None
        self.browser = None
        self._stealth = Stealth()

    def _get_random_proxy(self) -> Optional[dict]:
        """Select a random proxy from the available list."""
        if not self.proxies:
            return None
        proxy_url = random.choice(self.proxies)
        return {"server": proxy_url}

    async def start(self):
        """Launch the browser."""
        if not self.playwright:
            self.playwright = await async_playwright().start()

        # Launch browser without a fixed proxy to allow per-context proxies
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        logger.info("Browser launched.")

    async def stop(self):
        """Clean up resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser and Playwright stopped.")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def _create_context(self) -> BrowserContext:
        """Create a new browser context with a random proxy and User-Agent."""
        proxy = self._get_random_proxy()
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        if proxy:
            context_options["proxy"] = proxy
            logger.info(f"Using proxy for context: {proxy['server']}")

        return await self.browser.new_context(**context_options)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=20),
        retry=(retry_if_exception_type((Exception, ScrapingBlockError))),
        reraise=True,
        before_sleep=lambda retry_state: logger.info(f"Retrying ({retry_state.attempt_number}/5) after error: {retry_state.outcome.exception()}")
    )
    async def fetch_page(self, url: str, timeout: int = 60000) -> str:
        """
        Fetch the page source of a given URL with per-context proxy rotation,
        stealth, and human-like delays.

        :param url: The URL to fetch.
        :param timeout: Navigation timeout in milliseconds.
        :return: The page source as a string.
        """
        if not self.browser:
            await self.start()

        # Create a fresh context for each main request to rotate proxy/identity
        context = await self._create_context()
        page = await context.new_page()

        # Apply stealth
        await self._stealth.apply_stealth_async(page)

        try:
            # Random human-like delay before the request (jitter)
            pre_delay = random.uniform(2.0, 5.0)
            logger.info(f"Waiting {pre_delay:.2f}s jitter before navigation...")
            await asyncio.sleep(pre_delay)

            logger.info(f"Navigating to {url}")
            response = await page.goto(url, wait_until="networkidle", timeout=timeout)

            if not response:
                raise ScrapingBlockError("No response received (possibly blocked)")

            status = response.status
            if status in [403, 429]:
                raise ScrapingBlockError(f"Received block status code: {status}")

            if status >= 400:
                logger.warning(f"Received non-200 status code: {status}")

            # Post-load jitter
            post_delay = random.uniform(1.0, 3.0)
            await asyncio.sleep(post_delay)

            source = await page.content()

            # Check for common bot detection strings in content
            if "captcha" in source.lower() or "bot detection" in source.lower() or "challenge-running" in source.lower():
                raise ScrapingBlockError("Bot detection signature found in page content")

            return source
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            raise
        finally:
            await context.close()

if __name__ == "__main__":
    # Basic usage example
    async def main():
        async with BaseScraper(headless=True) as scraper:
            try:
                content = await scraper.fetch_page("https://example.com")
                print(f"Fetched content length: {len(content)}")
            except Exception as e:
                print(f"Final failure: {e}")

    asyncio.run(main())
