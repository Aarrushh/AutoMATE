import asyncio
import json
import logging
import random
import re
from datetime import datetime
from playwright.async_api import async_playwright

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

COMMON_APPS = {
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
}

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

    async def scrape_url(self, page, url):
        """Scrapes a single Zapier template URL."""
        try:
            logger.info(f"Scraping Zapier URL: {url}")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            if response and response.status >= 400:
                logger.error(f"Zapier URL {url} returned status {response.status}")
                return None

            # Try to extract __NEXT_DATA__ for structured info
            next_data_el = await page.query_selector("script#__NEXT_DATA__")
            if next_data_el:
                content = await next_data_el.inner_text()
                data = json.loads(content)
                template_data = data.get("props", {}).get("pageProps", {}).get("template", {})

                if template_data:
                    steps = template_data.get("steps", [])
                    trigger_app = "Unknown"
                    action_apps = []

                    if steps:
                        trigger_app = steps[0].get("app", {}).get("name", "Unknown")
                        action_apps = [s.get("app", {}).get("name") for s in steps[1:] if s.get("app")]

                    if not action_apps:
                        action_apps = ["Unknown Action"]

                    return {
                        "name": template_data.get("title") or "Unknown Zapier Template",
                        "description": template_data.get("description") or "",
                        "url": url,
                        "source_platform": "Zapier",
                        "trigger_app": trigger_app,
                        "action_apps": action_apps,
                        "raw_data": template_data
                    }

            # Fallback to selectors and regex
            title_el = await page.query_selector("h1")
            title = await title_el.inner_text() if title_el else "Unknown Zapier Template"

            tools = []
            for app in COMMON_APPS:
                if re.search(r'\b' + re.escape(app) + r'\b', title, re.IGNORECASE):
                    tools.append(app)

            return {
                "name": title.strip(),
                "description": title.strip(),
                "url": url,
                "source_platform": "Zapier",
                "trigger_app": tools[0] if tools else "Unknown",
                "action_apps": tools[1:] if len(tools) > 1 else ["Unknown Action"],
                "raw_data": {"url": url}
            }
        except Exception as e:
            self.log_error(f"Error scraping Zapier URL {url}: {e}")
            return None

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
                # Retry loop
                for attempt in range(3):
                    try:
                        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
                        break
                    except Exception as e:
                        if attempt == 2: raise
                        await asyncio.sleep(5)

                # Discover Categories
                categories = await self.discover_categories(page)
                if not categories:
                    categories = [
                        ("Lead management", "https://zapier.com/templates/lead-management"),
                        ("Sales pipeline", "https://zapier.com/templates/sales-pipeline"),
                        ("Marketing campaigns", "https://zapier.com/templates/marketing-campaigns"),
                        ("Customer support", "https://zapier.com/templates/customer-support"),
                        ("Data management", "https://zapier.com/templates/data-management"),
                        ("Project management", "https://zapier.com/templates/project-management")
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
            await asyncio.sleep(3)
            
            await self.extract_templates_from_page(page, category_name)
            await self.scroll_page(page, category_name)

        except Exception as e:
            self.log_error(f"Error in category {category_name}: {e}")

    async def scroll_page(self, page, category):
        last_height = await page.evaluate("document.body.scrollHeight")
        for i in range(15): 
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2.5) 
            await self.extract_templates_from_page(page, category)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    async def extract_templates_from_page(self, page, category):
        cards = await page.query_selector_all("a._zapCard_1g2fs_17")
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

            tools = []
            for app in COMMON_APPS:
                if re.search(r'\b' + re.escape(app) + r'\b', name, re.IGNORECASE):
                    tools.append(app)
            
            tag_el = await card.query_selector("._tagText_1g2fs_226")
            tag = await tag_el.inner_text() if tag_el else "Unknown"

            template = {
                "name": name.strip(),
                "description": name.strip(),
                "category": category,
                "type": tag,
                "tools": tools,
                "url": full_url
            }
            
            self.templates.append(template)
            self.seen_urls.add(url)
            self.total_scraped += 1
            
            if self.total_scraped % 50 == 0:
                logger.info(f"Progress: {self.total_scraped} templates scraped total")
                self.save_data()

    def save_data(self):
        data = {
            "total_count": len(self.templates),
            "scrape_date": datetime.now().isoformat(),
            "source": "zapier",
            "data": self.templates
        }
        try:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.log_error(f"Failed to save JSON: {e}")

if __name__ == "__main__":
    scraper = ZapierScraper()
    asyncio.run(scraper.scrape())
    print(f"Scraped {scraper.total_scraped} templates from Zapier successfully")
