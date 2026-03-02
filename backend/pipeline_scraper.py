import asyncio
import aiohttp
import json
import logging
import os
import random
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DATA_DIR = "backend/raw_data"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

class AsyncScraper:
    def __init__(self):
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        self.semaphore = asyncio.Semaphore(5) # Limit concurrency

    async def fetch_page(self, session, url):
        async with self.semaphore:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            try:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.error(f"Failed to fetch {url}: Status {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return None

    def extract_next_data(self, html):
        if not html:
            return None
        soup = BeautifulSoup(html, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag:
            try:
                return json.loads(script_tag.string)
            except json.JSONDecodeError:
                return None
        return None

    async def scrape_zapier(self):
        logger.info("Starting Zapier async scrape...")
        # In a real scenario, we'd discover categories first.
        # For this skeleton, we'll hit a few main ones and extract __NEXT_DATA__
        urls = [
            "https://zapier.com/templates",
            "https://zapier.com/templates/lead-management",
            "https://zapier.com/templates/sales-pipeline",
            "https://zapier.com/templates/marketing-campaigns",
            "https://zapier.com/templates/customer-support"
        ]

        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_page(session, url) for url in urls]
            pages = await asyncio.gather(*tasks)

            for i, html in enumerate(pages):
                data = self.extract_next_data(html)
                if data:
                    filename = f"zapier_{i}_{datetime.now().timestamp()}.json"
                    with open(os.path.join(RAW_DATA_DIR, filename), 'w') as f:
                        json.dump(data, f)
                    logger.info(f"Saved Zapier raw data to {filename}")

    async def scrape_make(self):
        logger.info("Starting Make.com async scrape...")
        # Make.com also uses Next.js often, or similar structures.
        urls = [
            "https://www.make.com/en/templates",
            "https://www.make.com/en/templates/category/marketing",
            "https://www.make.com/en/templates/category/sales"
        ]
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_page(session, url) for url in urls]
            pages = await asyncio.gather(*tasks)

            for i, html in enumerate(pages):
                data = self.extract_next_data(html)
                if data:
                    filename = f"make_{i}_{datetime.now().timestamp()}.json"
                    with open(os.path.join(RAW_DATA_DIR, filename), 'w') as f:
                        json.dump(data, f)
                    logger.info(f"Saved Make.com raw data to {filename}")

    async def scrape_n8n(self):
        logger.info("Starting n8n async scrape...")
        # n8n templates are often available via an API or hidden in the page.
        # We'll simulate fetching a few template pages.
        urls = ["https://n8n.io/workflows/"]
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_page(session, url) for url in urls]
            pages = await asyncio.gather(*tasks)
            for i, html in enumerate(pages):
                if html:
                    filename = f"n8n_{i}_{datetime.now().timestamp()}.html"
                    with open(os.path.join(RAW_DATA_DIR, filename), 'w') as f:
                        f.write(html)
                    logger.info(f"Saved n8n raw data to {filename}")

    async def scrape_github(self):
        logger.info("Starting GitHub async scrape...")
        # Search for automation templates / workflows
        topics = ["zapier-templates", "n8n-workflows", "make-com-templates", "github-actions"]
        async with aiohttp.ClientSession() as session:
            for topic in topics:
                url = f"https://github.com/topics/{topic}"
                html = await self.fetch_page(session, url)
                if html:
                    filename = f"github_{topic}_{datetime.now().timestamp()}.html"
                    with open(os.path.join(RAW_DATA_DIR, filename), 'w') as f:
                        f.write(html)
                    logger.info(f"Saved GitHub topic {topic} to {filename}")

    async def run_all(self):
        await asyncio.gather(
            self.scrape_zapier(),
            self.scrape_make(),
            self.scrape_n8n(),
            self.scrape_github()
        )

if __name__ == "__main__":
    scraper = AsyncScraper()
    asyncio.run(scraper.run_all())
