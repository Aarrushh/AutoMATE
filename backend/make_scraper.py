import logging
import json
from backend.scraper_base import BaseScraper
from backend.schema import AutomationTemplate, MaintenanceLevel

logger = logging.getLogger(__name__)

class MakeScraper(BaseScraper):
    def __init__(self, proxy_url: str = None):
        super().__init__(proxy_url)
        self.source_platform = "Make.com"

    async def scrape_url(self, url: str) -> AutomationTemplate:
        page, context = await self.fetch_page(url)
        try:
            # Extract title
            title_el = await page.query_selector("h1[data-test-id='template-name']")
            if not title_el:
                title_el = await page.query_selector("h1")
            name = await title_el.inner_text() if title_el else "Make.com Template"

            # Extract description
            desc_el = await page.query_selector("[data-test-id='template-description']")
            description = await desc_el.inner_text() if desc_el else name

            # Identify apps
            modules = await page.query_selector_all("[data-test-id='module']")
            apps = []
            seen_apps = set()
            for module in modules:
                img = await module.query_selector("img")
                if img:
                    alt = await img.get_attribute("alt")
                    if alt and alt not in seen_apps:
                        apps.append(alt.strip())
                        seen_apps.add(alt.strip())

            trigger_app = apps[0] if apps else "Unknown Trigger"
            action_apps = apps[1:] if len(apps) > 1 else ["Unknown Action"]

            # Heuristic scoring
            complexity_score = min(5, (len(apps) + 1) // 2)
            maintenance_level = MaintenanceLevel.LOW if complexity_score < 3 else MaintenanceLevel.MEDIUM
            monthly_opex = 9.0 + (len(action_apps) - 1) * 4.0

            template = AutomationTemplate(
                name=name,
                description=description,
                url=url,
                source_platform=self.source_platform,
                trigger_app=trigger_app,
                action_apps=action_apps,
                complexity_score=max(1, complexity_score),
                maintenance_level=maintenance_level,
                monthly_opex=max(0, monthly_opex),
                raw_data={"scraped_apps": apps}
            )
            return template
        finally:
            await page.close()
            await context.close()
