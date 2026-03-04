import asyncio
import json
import logging
import random
import re
from datetime import datetime
from playwright.async_api import async_playwright

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://zapier.com/templates"
OUTPUT_FILE = "templates_zapier.json"
ERROR_LOG_FILE = "error_log.txt"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

COMMON_APPS = sorted({
    "Slack", "Gmail", "Google Calendar", "HubSpot", "Salesforce", "Mailchimp", 
    "Airtable", "Trello", "Asana", "Discord", "Monday.com", "Notion", "Dropbox", 
    "Outlook", "Google Sheets", "Typeform", "Jira", "Zendesk", 
    "Facebook Lead Ads", "ActiveCampaign", "Pipedrive", "Shopify", "Stripe", 
    "Zoom", "Google Drive", "Twilio", "Intercom", "WordPress", "Calendly", 
    "Microsoft Teams", "QuickBooks", "Wave", "Xero", "WooCommerce", "ClickUp",
    "Basecamp", "Todoist", "ClickFunnels", "Leadpages", "Eventbrite", 
    "Zoho CRM", "Drip", "ConvertKit", "SendGrid", "WhatsApp", 
    "Telegram", "Instagram", "Facebook", "Twitter", "LinkedIn", "YouTube", 
    "TikTok", "Pinterest", "Reddit", "Snowflake", "BigQuery", "Looker",
    "Databricks", "Tableau", "Power BI", "Salesloft", "Google Forms", 
    "Cognito Forms", "Wufoo", "Gravity Forms", "SurveyMonkey", "Webflow"
})

COMPILED_APPS = [(app, re.compile(r'\b' + re.escape(app) + r'\b', re.IGNORECASE)) for app in COMMON_APPS]

class ZapierScraper:
    def __init__(self):
        self.templates = []
        self.seen_urls = set()
        self.total_scraped = 0
        self.load_existing()

    def load_existing(self):
        try:
            with open(OUTPUT_FILE, "r") as f:
                content = json.load(f)
                self.templates = content.get("data", [])
                self.seen_urls = {t["url"] for t in self.templates}
                self.total_scraped = len(self.templates)
                logger.info(f"Loaded {self.total_scraped} existing templates.")
        except:
            pass

    def log_error(self, message):
        timestamp = datetime.now().isoformat()
        with open(ERROR_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
        logger.error(message)

    async def scrape(self):
        async with async_playwright() as p:
            logger.info("Launching browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            try:
                logger.info(f"Navigating to {BASE_URL}")
                await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)

                categories = await self.discover_categories(page)
                if not categories:
                    categories = [
                        ("Lead management", "https://zapier.com/templates/lead-management"),
                        ("Sales pipeline", "https://zapier.com/templates/sales-pipeline")
                    ]
                
                logger.info(f"Working on {len(categories)} categories.")

                for category_name, category_url in categories:
                    await self.scrape_category(page, category_name, category_url)
                    await asyncio.sleep(2)

            except Exception as e:
                self.log_error(f"Scraper encountered a critical error: {str(e)}")
            finally:
                await browser.close()
                self.save_data()

    async def discover_categories(self, page):
        selector = "a[href*='/templates/']:not([href*='/details/'])"
        try:
            links = await page.query_selector_all(selector)
            categories = []
            for link in links:
                name = await link.inner_text()
                href = await link.get_attribute("href")
                if href and name.strip():
                    full_url = href if href.startswith("http") else f"https://zapier.com{href}"
                    if full_url not in [c[1] for c in categories]:
                        categories.append((name.strip(), full_url))
            return categories
        except:
            return []

    async def scrape_category(self, page, category_name, category_url):
        logger.info(f"Processing Category: {category_name}")
        try:
            await page.goto(category_url, wait_until="domcontentloaded", timeout=45000)

            # Use wait_for_function for better stability during scroll
            await page.wait_for_function("document.body.scrollHeight > 0")
            
            await self.extract_templates_from_page(page, category_name)
            await self.scroll_page(page, category_name)

        except Exception as e:
            self.log_error(f"Error in category {category_name}: {e}")

    async def scroll_page(self, page, category):
        last_height = await page.evaluate("document.body.scrollHeight")
        for i in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            await page.wait_for_function(f"document.body.scrollHeight > {last_height}", timeout=5000).catch(lambda e: None)

            await self.extract_templates_from_page(page, category)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    async def extract_templates_from_page(self, page, category):
        cards = await page.query_selector_all("a[href*='/templates/details/']")
        for card in cards:
            url = await card.get_attribute("href")
            if not url or url in self.seen_urls:
                continue
            
            full_url = url if url.startswith("http") else f"https://zapier.com{url}"
            
            name = await card.get_attribute("aria-label")
            if not name:
                name_el = await card.query_selector("span._title_1g2fs_134")
                name = await name_el.inner_text() if name_el else ""
            
            if not name:
                continue

            # App extraction logic
            found_apps = []
            for app_name, pattern in COMPILED_APPS:
                if pattern.search(name):
                    found_apps.append(app_name)
            
            # Distinguish trigger/actions based on name pattern "X to Y"
            trigger_app = found_apps[0] if found_apps else "Unknown"
            action_apps = found_apps[1:] if len(found_apps) > 1 else ["Unknown Action"]

            if " to " in name.lower():
                parts = re.split(r'\s+to\s+', name, flags=re.IGNORECASE)
                # This is a bit naive but follows user request to improve trigger/action splitting
                potential_trigger = parts[0].strip()
                for app_name, _ in COMPILED_APPS:
                    if app_name.lower() in potential_trigger.lower():
                        trigger_app = app_name
                        break

            template = {
                "title": name.strip(),
                "description": name.strip(),
                "category": category,
                "raw_apps": found_apps,
                "trigger_app": trigger_app,
                "action_apps": action_apps,
                "url": full_url,
                "source": "zapier"
            }
            
            self.templates.append(template)
            self.seen_urls.add(url)
            self.total_scraped += 1
            
            if self.total_scraped % 50 == 0:
                self.save_data()

    async def scrape_url(self, url):
        # Implementation for single URL scraping used in dry_run
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")

            title_el = await page.query_selector("h1")
            title = await title_el.inner_text() if title_el else "Unknown Title"

            found_apps = []
            for app_name, pattern in COMPILED_APPS:
                if pattern.search(title):
                    found_apps.append(app_name)

            await browser.close()
            return {
                "title": title,
                "description": title,
                "raw_apps": found_apps,
                "source": "zapier"
            }

    def save_data(self):
        data = {
            "total_count": len(self.templates),
            "scrape_date": datetime.now().isoformat(),
            "source": "zapier",
            "data": self.templates
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    scraper = ZapierScraper()
    asyncio.run(scraper.scrape())
