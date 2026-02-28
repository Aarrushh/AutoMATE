import asyncio
import json
import logging
import random
import time
from datetime import datetime
from playwright.async_api import async_playwright

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubScraper:
    def __init__(self, target_volume=2000):
        self.target_volume = target_volume
        self.user_agent = "Mozilla/5.0 (Compatible; OpenSourceResearchBot/1.0)"
        self.source_domains = [
            "https://github.com/topics/workflow-automation",
            "https://github.com/topics/business-automation",
            "https://github.com/topics/zapier-alternative",
            "https://github.com/topics/workflow-engine",
            "https://github.com/topics/low-code"
        ]
        self.output_path = "data/github_opensource_library.json"
        self.repos = []
        self.seen_urls = set()
        self.rate_limit = 5  # Adhering to 4-5 seconds per request constraint
        self.load_existing()

    def load_existing(self):
        try:
            with open(self.output_path, "r") as f:
                content = json.load(f)
                data = content.get("data", [])
                for item in data:
                    if item["url"] not in self.seen_urls:
                        self.seen_urls.add(item["url"])
                        # Minimal mapping back
                        self.repos.append({
                            "name": item["name"],
                            "description": item["description"],
                            "stars": item.get("stars", 0),
                            "language": item.get("language", "Unknown"),
                            "url": item["url"],
                            "tags": [item["category"]] if item.get("category") else [],
                            "tools": item["tools"],
                            "has_dockerfile": item["financials"]["estimated_operating_cost_per_month"] == 10.0
                        })
                logger.info(f"Loaded {len(self.repos)} existing records.")
        except Exception as e:
            logger.info(f"No existing data or error loading: {e}")

    async def wait_for_rate_limit(self):
        # logger.info(f"Rate limiting: waiting {self.rate_limit} seconds...")
        await asyncio.sleep(self.rate_limit)

    async def scrape_topic(self, page, topic_url):
        logger.info(f"Scraping topic: {topic_url}")
        await page.goto(topic_url)

        # Initial wait for content
        try:
            await page.wait_for_selector("article.border", timeout=10000)
        except:
            logger.warning(f"Timeout waiting for articles on {topic_url}")
            return

        # Click Load More until limit or no more button
        while len(self.repos) < self.target_volume:
            # Try multiple selectors for the 'Load more' button
            selectors = ["button:has-text('Load more')", ".ajax-pagination-btn", "form[data-ajax-with-lists-instrumentation] button"]
            target_selector = None
            for sel in selectors:
                if await page.query_selector(sel):
                    target_selector = sel
                    break

            if not target_selector:
                # One last try with a very broad search
                found = await page.evaluate("""() => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const btn = buttons.find(b => b.innerText.includes('Load more'));
                    if (btn) {
                        btn.setAttribute('id', 'temp-load-more-btn');
                        return true;
                    }
                    return false;
                }""")
                if found:
                    target_selector = "#temp-load-more-btn"

            if not target_selector:
                logger.info("No more 'Load more' button found.")
                break

            old_count = await page.evaluate("document.querySelectorAll('article.border').length")
            # logger.info(f"Clicking 'Load more'... (current page items: {old_count})")
            try:
                await page.click(target_selector, timeout=5000)
            except Exception as e:
                logger.warning(f"Failed to click {target_selector}: {e}")
                break

            try:
                # Wait for more items to load
                await page.wait_for_function(f"document.querySelectorAll('article.border').length > {old_count}", timeout=10000)
            except Exception as e:
                # logger.info("Timeout waiting for more articles or no more articles.")
                pass

            await self.wait_for_rate_limit()

            # Extract current items to check progress
            await self.extract_metadata(page)
            if len(self.repos) % 100 == 0:
                logger.info(f"Currently found {len(self.repos)} unique repositories.")
                self.save_data() # Save progress

            if len(self.repos) >= self.target_volume:
                break

    async def extract_metadata(self, page):
        results = await page.evaluate("""() => {
            const articles = Array.from(document.querySelectorAll('article.border'));
            return articles.map(article => {
                const urlEl = article.querySelector('h3.f3 a.text-bold');
                const descEl = article.querySelector('div.color-bg-default p.color-fg-muted');
                // The provided selector span#repo-stars-counter-star is for repo pages.
                // On topic pages, stars are in .Counter.js-social-count
                const starsEl = article.querySelector('.Counter.js-social-count');
                const langEl = article.querySelector('span[itemprop="programmingLanguage"]');
                const topicEls = Array.from(article.querySelectorAll('a.topic-tag'));

                return {
                    name: urlEl ? urlEl.innerText.trim() : '',
                    url: urlEl ? 'https://github.com' + urlEl.getAttribute('href') : '',
                    description: descEl ? descEl.innerText.trim() : '',
                    starsText: starsEl ? starsEl.innerText.trim() : '0',
                    language: langEl ? langEl.innerText.trim() : 'Unknown',
                    tags: topicEls.map(t => t.innerText.trim())
                };
            });
        }""")

        for item in results:
            if not item["url"] or item["url"] in self.seen_urls:
                continue

            stars = self.parse_stars(item["starsText"])
            repo_data = {
                "name": item["name"],
                "description": item["description"],
                "stars": stars,
                "language": item["language"],
                "url": item["url"],
                "tags": item["tags"],
                "tools": list(set([item["language"]] + item["tags"])),
                "has_dockerfile": any(t.lower() in ["docker", "dockerfile", "container"] for t in item["tags"])
            }
            self.repos.append(repo_data)
            self.seen_urls.add(item["url"])

    async def verify_dockerfile(self, page, repo):
        if repo.get("has_dockerfile"):
            return

        # logger.info(f"Verifying Dockerfile for {repo['name']}...")
        try:
            await page.goto(repo["url"], wait_until="domcontentloaded", timeout=30000)
            content = await page.content()
            if "Dockerfile" in content:
                repo["has_dockerfile"] = True
            else:
                repo["has_dockerfile"] = False
        except Exception as e:
            pass

        await asyncio.sleep(self.rate_limit)

    def parse_stars(self, text):
        text = text.strip().lower()
        if 'k' in text:
            try:
                return int(float(text.replace('k', '')) * 1000)
            except:
                return 0
        try:
            return int(text.replace(',', ''))
        except:
            return 0

    def enrich_and_classify(self):
        enriched_data = []
        for repo in self.repos:
            # Cost Calculation
            infra_cost = 5.00 # Default VPS
            if repo["language"] in ["Python", "JavaScript", "TypeScript"]:
                infra_cost = 0.00 # Serverless

            if repo["has_dockerfile"]:
                infra_cost = 10.00 # Container

            complexity_score = 1
            if infra_cost == 5.00:
                complexity_score = 2
            elif infra_cost == 10.00:
                complexity_score = 3

            repo_type = "Open Source Workflow" # Default
            if repo["stars"] > 1000:
                repo_type = "High-Trust Community Solution"
            elif repo["language"] == "Python":
                repo_type = "Script-based Automation"

            enriched_repo = {
                "name": repo["name"],
                "description": repo["description"],
                "category": repo["tags"][0] if repo["tags"] else "Automation",
                "stars": repo.get("stars", 0),
                "language": repo.get("language", "Unknown"),
                "type": repo_type,
                "tools": repo["tools"],
                "url": repo["url"],
                "financials": {
                    "setup_cost": "Free (Open Source)",
                    "estimated_operating_cost_per_month": infra_cost,
                    "maintenance_load": "High (Requires Developer)"
                },
                "estimated_infrastructure_cost_monthly": infra_cost,
                "deployment_complexity_score": complexity_score
            }
            enriched_data.append(enriched_repo)
        return enriched_data

    def save_data(self):
        enriched_data = self.enrich_and_classify()
        output = {
            "total_count": len(enriched_data),
            "scrape_date": datetime.now().isoformat(),
            "source": "github_topics",
            "data": enriched_data
        }
        with open(self.output_path, "w") as f:
            json.dump(output, f, indent=2)

    async def scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()

            for domain in self.source_domains:
                await self.scrape_topic(page, domain)
                if len(self.repos) >= self.target_volume:
                    break

            # Verify Dockerfiles for a sample of repositories to enrich data quality
            # while respecting time and rate limit constraints.
            logger.info(f"Verifying Dockerfile for top 20 repositories...")
            for repo in self.repos[:20]:
                await self.verify_dockerfile(page, repo)

            await browser.close()
            self.save_data()
            logger.info(f"Scrape completed. Total: {len(self.repos)}")

if __name__ == "__main__":
    scraper = GitHubScraper(target_volume=2000)
    asyncio.run(scraper.scrape())
