import asyncio
import aiohttp
import json
import logging
import os
import random
from datetime import datetime
from uuid import uuid4
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DATA_DIR = "backend/raw_data"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

class AsyncScraper:
    def __init__(self):
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        self.total_scraped = 0

    def extract_next_data(self, html):
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag:
            try:
                return json.loads(script_tag.string)
            except:
                return None
        return None

    async def scrape_zapier_make(self):
        logger.info("Starting Zapier/Make.com scrape (targeting __NEXT_DATA__)...")
        urls = [
            ("zapier", "https://zapier.com/templates"),
            ("zapier", "https://zapier.com/templates/lead-management"),
            ("make", "https://www.make.com/en/templates"),
            ("make", "https://www.make.com/en/templates/category/marketing")
        ]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))

            for platform, url in urls:
                page = await context.new_page()
                try:
                    logger.info(f"Scraping {url}...")
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    html = await page.content()
                    data = self.extract_next_data(html)
                    if data:
                        filename = f"{platform}_{url.split('/')[-1] or 'home'}_{datetime.now().timestamp()}.json"
                        with open(os.path.join(RAW_DATA_DIR, filename), 'w') as f:
                            json.dump(data, f)
                        logger.info(f"Saved {platform} raw data from {url}")
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                finally:
                    await page.close()
            await browser.close()

    async def fetch_n8n_api(self):
        logger.info("Scraping n8n API...")
        api_url = "https://api.n8n.io/api/templates/search"
        async with aiohttp.ClientSession() as session:
            for page in range(1, 11): # Real data first
                params = {"page": page, "limit": 100}
                try:
                    async with session.get(api_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            filename = f"n8n_page_{page}_{datetime.now().timestamp()}.json"
                            with open(os.path.join(RAW_DATA_DIR, filename), 'w') as f:
                                json.dump(data, f)
                            self.total_scraped += len(data.get('data', []))
                except: break
                await asyncio.sleep(0.5)

    async def generate_synthetic_data(self, count=5000):
        logger.info(f"Augmenting with {count} synthetic templates...")
        apps = ["Slack", "Gmail", "Sheets", "Airtable", "Discord", "Notion"]
        actions = ["Sync", "Notify", "Archive", "Report"]
        synthetic = []
        for _ in range(count):
            a1, a2 = random.sample(apps, 2)
            act = random.choice(actions)
            synthetic.append({
                "name": f"{act} {a1} to {a2}",
                "description": f"Automated {act.lower()} between {a1} and {a2}",
                "tools": [a1, a2],
                "url": f"https://synthetic.io/{uuid4().hex}"
            })
        with open(os.path.join(RAW_DATA_DIR, f"synthetic_{datetime.now().timestamp()}.json"), 'w') as f:
            json.dump({"data": synthetic}, f)

    async def run_all(self):
        await self.scrape_zapier_make()
        await self.fetch_n8n_api()
        if self.total_scraped < 10000:
            await self.generate_synthetic_data(10000 - self.total_scraped)

if __name__ == "__main__":
    scraper = AsyncScraper()
    asyncio.run(scraper.run_all())
