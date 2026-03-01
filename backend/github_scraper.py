import asyncio
import json
import os
import random
import re
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration from task
TARGET_TOPICS = [
    "workflow-automation",
    "business-automation",
    "zapier-alternative",
    "no-code-automation",
    "marketing-automation",
    "automation-workflows",
    "robotic-process-automation",
    "low-code-platform",
    "ai-automation",
    "workflow-engine",
    "integration-platform",
    "automation-tools",
    "open-source-automation",
    "self-hosted-automation",
    "devops-automation",
    "cloud-automation"
]
BASE_TOPIC_URL = "https://github.com/topics/"
OUTPUT_PATH = "data/github_opensource_library.json"
USER_AGENT = "Mozilla/5.0 (Compatible; OpenSourceResearchBot/1.0)"

# Rate limit: 1 request per 4-5 seconds
DELAY = 5

class GitHubScraper:
    def __init__(self):
        self.data = []
        self.seen_urls = set()

    def cost_calculation(self, language, topics, description):
        has_docker = any("docker" in t.lower() or "container" in t.lower() for t in topics) or \
                     "dockerfile" in description.lower()
        is_serverless_lang = language in ["Python", "JavaScript", "TypeScript"]
        setup_cost = "Free (Open Source)"
        if has_docker:
            operating_cost = 10.0
            complexity = 3
            infra_type = "Container"
        elif is_serverless_lang:
            operating_cost = 0.0
            complexity = 1
            infra_type = "Serverless"
        else:
            operating_cost = 5.0
            complexity = 2
            infra_type = "VPS"
        return {
            "setup_cost": setup_cost,
            "estimated_operating_cost_per_month": operating_cost,
            "maintenance_load": "High (Requires Developer)",
            "deployment_complexity_score": complexity,
            "infra_type": infra_type
        }

    def type_classification(self, stars, language):
        if stars > 1000:
            return "High-Trust Community Solution"
        elif language == "Python":
            return "Script-based Automation"
        else:
            return "Open Source Workflow"

    async def scrape(self):
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            for topic in TARGET_TOPICS:
                if len(self.data) >= 3000: break
                url = f"{BASE_TOPIC_URL}{topic}"
                print(f"Processing Topic: {topic}")
                await self.scrape_topic(page, url, topic)
                await asyncio.sleep(DELAY)

            await browser.close()
            self.save_results()

    async def scrape_topic(self, page, url, category):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(2)

            while len(self.data) < 3000:
                initial_count = len(self.data)
                await self.extract_from_page(page, category)

                if len(self.data) > initial_count:
                    print(f"Found {len(self.data) - initial_count} new items. Total: {len(self.data)}")
                    if len(self.data) % 100 == 0:
                        self.save_results()

                load_more_btn = await page.query_selector("button:has-text('Load more')")
                if not load_more_btn:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                    load_more_btn = await page.query_selector("button:has-text('Load more')")
                    if not load_more_btn:
                        print(f"No more results for {category}")
                        break

                print(f"Clicking Load More... (Current total: {len(self.data)})")
                await load_more_btn.scroll_into_view_if_needed()
                await load_more_btn.click()
                await asyncio.sleep(DELAY)

        except Exception as e:
            print(f"Error scraping topic {category}: {e}")

    async def extract_from_page(self, page, primary_topic):
        articles = await page.query_selector_all("article.border")
        for article in articles:
            try:
                name_el = await article.query_selector("h3.f3 a.text-bold")
                if not name_el: continue

                href = await name_el.get_attribute("href")
                url = f"https://github.com{href}"

                if url in self.seen_urls:
                    continue

                name = (await name_el.inner_text()).strip()
                desc_el = await article.query_selector("div.color-bg-default p.color-fg-muted")
                description = (await desc_el.inner_text()).strip() if desc_el else ""

                stars_el = await article.query_selector("span#repo-stars-counter-star")
                stars_str = await stars_el.get_attribute("aria-label") if stars_el else "0"
                stars = self.parse_stars(stars_str)

                lang_el = await article.query_selector("span[itemprop='programmingLanguage']")
                language = (await lang_el.inner_text()).strip() if lang_el else "Unknown"

                topic_els = await article.query_selector_all("a.topic-tag")
                topics = []
                for t in topic_els:
                    topics.append((await t.inner_text()).strip())

                financials = self.cost_calculation(language, topics, description)
                repo_type = self.type_classification(stars, language)

                repo_data = {
                    "name": name,
                    "description": description,
                    "category": primary_topic,
                    "type": repo_type,
                    "tools": list(set(topics + [language])),
                    "url": url,
                    "financials": {
                        "setup_cost": financials["setup_cost"],
                        "estimated_operating_cost_per_month": financials["estimated_operating_cost_per_month"],
                        "maintenance_load": financials["maintenance_load"]
                    },
                    "estimated_infrastructure_cost_monthly": financials["estimated_operating_cost_per_month"],
                    "deployment_complexity_score": financials["deployment_complexity_score"],
                    "stars": stars
                }

                self.data.append(repo_data)
                self.seen_urls.add(url)

                if len(self.data) >= 3000:
                    return

            except Exception as e:
                pass

    def parse_stars(self, stars_str):
        if not stars_str: return 0
        match = re.search(r'([\d\.,]+)([kK]?)', stars_str)
        if not match:
            return 0
        num_str = match.group(1).replace(',', '')
        suffix = match.group(2).lower()
        try:
            num = float(num_str)
            if suffix == 'k':
                num *= 1000
            return int(num)
        except:
            return 0

    def save_results(self):
        output = {
            "total_count": len(self.data),
            "scrape_date": datetime.now().isoformat(),
            "source": "github_topics",
            "data": self.data
        }
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Saved {len(self.data)} repositories to {OUTPUT_PATH}")

if __name__ == "__main__":
    scraper = GitHubScraper()
    asyncio.run(scraper.scrape())
