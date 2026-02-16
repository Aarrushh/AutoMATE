import asyncio
import json
import logging
import random
import os
import time
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TARGET_URLS = [
    "https://github.com/topics/workflow-automation",
    "https://github.com/topics/business-automation",
    "https://github.com/topics/zapier-alternative",
    "https://github.com/topics/no-code",
    "https://github.com/topics/low-code",
    "https://github.com/topics/marketing-automation",
    "https://github.com/topics/rpa"
]

OUTPUT_FILE = "data/github_opensource_library.json"
TARGET_VOLUME_MIN = 2000
TARGET_VOLUME_MAX = 3000

class GitHubScraper:
    def __init__(self):
        self.repos = []
        self.seen_urls = set()
        self.total_scraped = 0
        self.processed_indices = {} # Map url -> count of processed items to skip
        self.load_existing()

    def load_existing(self):
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, "r") as f:
                    data = json.load(f)
                    self.repos = data
                    self.seen_urls = {item["url"] for item in data}
                    self.total_scraped = len(data)
                    logger.info(f"Loaded {self.total_scraped} existing repos.")
            except Exception as e:
                logger.error(f"Failed to load existing data: {e}")

    async def scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Compatible; OpenSourceResearchBot/1.0)",
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            for url in TARGET_URLS:
                if self.total_scraped >= TARGET_VOLUME_MAX:
                    break
                await self.scrape_topic(page, url)

            await browser.close()
            self.save_data()
            logger.info(f"Scraping complete. Total repos: {self.total_scraped}")

    async def scrape_topic(self, page, url):
        logger.info(f"Navigating to {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            logger.error(f"Failed to load {url}: {e}")
            return

        topic_processed_count = 0

        while self.total_scraped < TARGET_VOLUME_MAX:
            # Wait for articles to be present
            try:
                await page.wait_for_selector("article.border", timeout=5000)
            except:
                logger.warning("No articles found on page.")
                break

            # Extract current page repos
            all_repos = await page.query_selector_all("article.border")
            new_repos_elements = all_repos[topic_processed_count:]

            if not new_repos_elements:
                logger.info("No new repos found on this scan.")

            for repo in new_repos_elements:
                if self.total_scraped >= TARGET_VOLUME_MAX:
                    break

                await self.process_repo(repo)
                topic_processed_count += 1

            if self.total_scraped >= TARGET_VOLUME_MAX:
                break

            # Click load more
            load_more_button = None
            try:
                load_more_button = page.get_by_role("button", name="Load more")
                if not await load_more_button.is_visible():
                     load_more_button = await page.query_selector(".ajax-pagination-btn")
            except:
                pass

            if load_more_button and await load_more_button.is_visible():
                try:
                    await load_more_button.click()
                    logger.info("Clicked 'Load more'. Waiting for rate limit...")
                    await asyncio.sleep(random.uniform(4, 5)) # Strict Rate Limit
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception as e:
                    logger.warning(f"Error clicking Load More: {e}")
                    break
            else:
                logger.info("No 'Load more' button visible. End of topic.")
                break

    async def process_repo(self, repo_handle):
        try:
            # Name & URL
            name_el = await repo_handle.query_selector("h3.f3 a.text-bold")
            if not name_el: return
            name = await name_el.inner_text()
            url = await name_el.get_attribute("href")
            full_url = f"https://github.com{url}" if url and url.startswith("/") else url

            if not full_url or full_url in self.seen_urls:
                return

            # Description
            desc_el = await repo_handle.query_selector("div.color-bg-default p.color-fg-muted")
            description = await desc_el.inner_text() if desc_el else ""

            # Category (Topic Tag)
            topic_tags = await repo_handle.query_selector_all("a.topic-tag")
            topics = [await t.inner_text() for t in topic_tags]
            category = topics[0].strip() if topics else "Unknown"

            # Stars
            stars = 0
            star_el = await repo_handle.query_selector("span#repo-stars-counter-star")
            if not star_el:
                 # Fallback
                 star_el = await repo_handle.query_selector(".Counter.js-social-count")

            if star_el:
                stars_text = await star_el.inner_text()
                stars = self.parse_stars(stars_text)

            # Language
            lang_el = await repo_handle.query_selector("span[itemprop='programmingLanguage']")
            language = await lang_el.inner_text() if lang_el else "Unknown"

            # Enrichment
            infra_cost, complexity = self.calculate_cost(language, topics)
            repo_type = self.classify_type(stars, language)

            # Tools
            tools_list = [t.strip() for t in topics]
            if language and language != "Unknown" and language not in tools_list:
                tools_list.append(language)

            repo_data = {
                "name": name.strip(),
                "description": description.strip(),
                "category": category,
                "type": repo_type,
                "tools": tools_list,
                "url": full_url,
                "financials": {
                    "setup_cost": "Free (Open Source)",
                    "estimated_operating_cost_per_month": infra_cost,
                    "maintenance_load": "High (Requires Developer)",
                    "deployment_complexity_score": complexity
                }
            }

            self.repos.append(repo_data)
            self.seen_urls.add(full_url)
            self.total_scraped += 1

            if self.total_scraped % 50 == 0:
                 logger.info(f"Total scraped: {self.total_scraped}")
                 self.save_data()

        except Exception as e:
            logger.error(f"Error parsing repo: {e}")

    def parse_stars(self, text):
        text = text.strip()
        try:
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            return int(text.replace(',', ''))
        except:
            return 0

    def calculate_cost(self, language, topics):
        cost = 5.00 # Default VPS
        complexity = "Medium" # Default

        # Check Language
        if language in ["Python", "JavaScript", "TypeScript", "Node.js"]:
            cost = 0.00
            complexity = "Low"

        # Check Docker (Heuristic via topics)
        is_docker = any("docker" in t.lower() for t in topics)
        if is_docker:
            cost = 10.00
            complexity = "High"

        return cost, complexity

    def classify_type(self, stars, language):
        if stars > 1000:
            return "High-Trust Community Solution"
        if language == "Python":
            return "Script-based Automation"
        return "Open Source Workflow"

    def save_data(self):
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(self.repos, f, indent=2)

if __name__ == "__main__":
    scraper = GitHubScraper()
    asyncio.run(scraper.scrape())
