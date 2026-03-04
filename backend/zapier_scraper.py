import asyncio
import json
import logging
import re
from typing import List
from .scraper_base import BaseScraper
from .schema import AutomationTemplate
from .heuristic_engine import HeuristicEngine

logger = logging.getLogger(__name__)

class ZapierScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://zapier.com/templates")
        self.output_file = "templates_zapier_v2.json"

    async def scrape(self):
        await self.init_browser()
        page = await self.context.new_page()

        try:
            if await self.safe_goto(page, self.base_url):
                categories = await self.discover_categories(page)
                logger.info(f"Discovered {len(categories)} categories.")

                # For testing, we might want to limit the number of categories
                for name, url in categories[:2]:
                    await self.scrape_category(page, name, url)
        finally:
            await self.close_browser()
            self.save_results()

    async def discover_categories(self, page):
        selector = "a[href*='/templates/']:not([href*='/details/'])"
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

    async def scrape_category(self, page, category_name, category_url):
        logger.info(f"Scraping category: {category_name}")
        if await self.safe_goto(page, category_url):
            # Extract cards
            cards = await page.query_selector_all("a[href*='/templates/details/']")
            urls = []
            for card in cards:
                href = await card.get_attribute("href")
                if href:
                    full_url = href if href.startswith("http") else f"https://zapier.com{href}"
                    if full_url not in urls:
                        urls.append(full_url)

            logger.info(f"Found {len(urls)} template URLs in category {category_name}")
            for url in urls[:5]: # Limit for initial development
                result = await self.scrape_template_details(page, url)
                if result:
                    # Integrate HeuristicEngine
                    complexity = HeuristicEngine.calculate_complexity(result["trigger_app"], result["action_apps"])
                    maintenance = HeuristicEngine.determine_maintenance(complexity)
                    opex = HeuristicEngine.estimate_opex(result["trigger_app"], result["action_apps"])

                    # Validate against Pydantic model
                    try:
                        template = AutomationTemplate(
                            title=result["title"],
                            description=result["description"],
                            source_url=result["source_url"],
                            trigger_app=result["trigger_app"],
                            action_apps=result["action_apps"],
                            complexity_score=complexity,
                            maintenance_level=maintenance,
                            monthly_opex=opex,
                            raw_data=result["raw_data"]
                        )
                        self.results.append(template)
                        logger.info(f"Successfully scraped and validated: {template.title}")
                    except Exception as e:
                        logger.error(f"Validation failed for {result['title']}: {e}")

    async def scrape_template_details(self, page, url):
        logger.info(f"Scraping details for: {url}")
        if await self.safe_goto(page, url):
            await asyncio.sleep(2)
            try:
                title_el = await page.query_selector("h1")
                if not title_el:
                    return None
                title = await title_el.inner_text()

                # Extract description
                description = ""
                desc_el = await page.query_selector("p._root_5qg8s_1")
                if desc_el:
                    description = await desc_el.inner_text()

                # Extract apps
                all_found_apps = await self.extract_all_apps(page, title)
                trigger_app, action_apps = self.parse_trigger_actions(title, all_found_apps)

                # If we couldn't separate them, but found apps, assign them reasonably
                if trigger_app == "Unknown" and all_found_apps:
                    if len(all_found_apps) >= 2:
                        # Guess: first is trigger, rest are actions
                        trigger_app = all_found_apps[0]
                        action_apps = all_found_apps[1:]
                    else:
                        trigger_app = all_found_apps[0]
                        action_apps = []

                # Final fallback
                if trigger_app == "Unknown":
                    trigger_app = "Manual Trigger"

                return {
                    "title": title.strip(),
                    "description": description.strip(),
                    "source_url": url,
                    "trigger_app": trigger_app,
                    "action_apps": action_apps,
                    "raw_data": {"url": url}
                }
            except Exception as e:
                logger.error(f"Error parsing template at {url}: {e}")
        return None

    async def extract_all_apps(self, page, title):
        apps = set()
        # From logos - focus on template specific images
        logos = await page.query_selector_all("img[alt*='logo'], img[alt*='Logo'], img[alt*='icon'], img[alt*='Icon']")
        for logo in logos:
            alt = await logo.get_attribute("alt")
            src = await logo.get_attribute("src") or ""

            # Filter to images that look like app logos in the template area
            if alt and ("zapier-images" in src or "/generated/" in src):
                # Clean up the alt text to get the app name
                app = alt.lower()
                for suffix in [" logo", " icon", "-logo", "-icon"]:
                    app = app.replace(suffix, "")
                app = app.strip()

                # Filter out generic/meta icons
                if app in ["mcp", "company", "powered by onetrust", "zapier", "graphic", "implement ai", "google"]:
                    continue

                # Capitalize nicely
                apps.add(app.title())

        # From title matching (using a base list)
        common_apps = [
            "Slack", "Asana", "Gmail", "Google Sheets", "Trello", "ClickUp",
            "HubSpot", "Salesforce", "Notion", "Airtable", "ActiveCampaign",
            "Typeform", "Jira", "Zendesk", "Shopify", "Stripe", "Zoom",
            "Twilio", "Mailchimp", "Discord", "Monday.com", "Dropbox",
            "Outlook", "Google Drive", "WordPress", "Calendly",
            "Microsoft Teams", "QuickBooks", "Webhooks", "AWS", "Python"
        ]
        for app in common_apps:
            if re.search(r'\b' + re.escape(app) + r'\b', title, re.IGNORECASE):
                apps.add(app)

        return list(apps)

    def parse_trigger_actions(self, title, all_found_apps):
        trigger_app = "Unknown"
        action_apps = []

        # Try pattern: "... from [Trigger] to [Action]"
        match = re.search(r"from (.*) to (.*)", title, re.IGNORECASE)
        if match:
            trigger_part = match.group(1)
            action_part = match.group(2)
            for app in all_found_apps:
                if app.lower() in trigger_part.lower():
                    trigger_app = app
                elif app.lower() in action_part.lower():
                    if app not in action_apps:
                        action_apps.append(app)
            if trigger_app != "Unknown":
                return trigger_app, action_apps

        # Try pattern: "[Action] from [Trigger]"
        if " from " in title:
            parts = title.split(" from ")
            action_part = parts[0]
            trigger_part = parts[1]
            for app in all_found_apps:
                if app.lower() in trigger_part.lower():
                    trigger_app = app
                elif app.lower() in action_part.lower():
                    if app not in action_apps:
                        action_apps.append(app)
            if trigger_app != "Unknown":
                return trigger_app, action_apps

        # Try pattern: "[Trigger] to [Action]"
        if " to " in title:
            parts = title.split(" to ")
            trigger_part = parts[0]
            action_part = parts[1]
            for app in all_found_apps:
                if app.lower() in trigger_part.lower():
                    trigger_app = app
                elif app.lower() in action_part.lower():
                    if app not in action_apps:
                        action_apps.append(app)
            if trigger_app != "Unknown":
                return trigger_app, action_apps

        return trigger_app, action_apps

    def save_results(self):
        with open(self.output_file, "w") as f:
            json.dump([r.model_dump(mode='json') for r in self.results], f, indent=2)
        logger.info(f"Saved {len(self.results)} results to {self.output_file}")

if __name__ == "__main__":
    scraper = ZapierScraper()
    asyncio.run(scraper.scrape())
