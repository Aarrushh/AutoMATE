import logging
import re
import json
from backend.scraper_base import BaseScraper
from backend.schema import AutomationTemplate, MaintenanceLevel

logger = logging.getLogger(__name__)

class ZapierScraper(BaseScraper):
    def __init__(self, proxy_url: str = None):
        super().__init__(proxy_url)
        self.source_platform = "Zapier"

    async def scrape_url(self, url: str) -> AutomationTemplate:
        page, context = await self.fetch_page(url)
        try:
            # Try to extract from __NEXT_DATA__ first for high-fidelity data
            next_data_script = await page.query_selector("script#__NEXT_DATA__")
            if next_data_script:
                try:
                    data_text = await next_data_script.inner_text()
                    data = json.loads(data_text)
                    # Often Zapier template data is in props.pageProps.template
                    # template_data = data.get("props", {}).get("pageProps", {}).get("template", {})
                except Exception as e:
                    logger.debug(f"Failed to parse __NEXT_DATA__: {e}")
            
            # DOM-based extraction
            apps = []
            seen_apps = set()
            
            # Look for step items which usually contain the app name/logo
            steps = await page.query_selector_all("div[data-testid*='step'], div[class*='Step'], div[class*='Card']")
            for step in steps:
                # Prioritize image alt text or span text within the step
                app_el = await step.query_selector("img[alt], span[class*='AppName'], div[class*='Title']")
                if app_el:
                    alt = await app_el.get_attribute("alt")
                    text = await app_el.inner_text()
                    name = alt or text
                    if name:
                        # Clean name (e.g., "Slack logo" -> "Slack")
                        name = re.sub(r'\s+logo$', '', name, flags=re.IGNORECASE).strip()
                        if name and name not in seen_apps and len(name) < 50:
                            apps.append(name)
                            seen_apps.add(name)
            
            if not apps:
                # Fallback to title parsing
                title_el = await page.query_selector("h1")
                title = await title_el.inner_text() if title_el else ""
                if " to " in title:
                    apps = [app.strip() for app in title.split(" to ")]
                elif " from " in title:
                    parts = title.split(" from ")
                    apps = [parts[1].strip(), parts[0].strip()]

            trigger_app = apps[0] if apps else "Unknown Trigger"
            action_apps = apps[1:] if len(apps) > 1 else ["Unknown Action"]
            
            name_el = await page.query_selector("h1")
            name = await name_el.inner_text() if name_el else "Zapier Template"
            
            desc_el = await page.query_selector("div[class*='Description'], p")
            description = await desc_el.inner_text() if desc_el else name

            # Heuristic scoring
            complexity_score = min(5, (len(apps) + 1) // 2 + (1 if any(a.lower() in ["webhooks", "code", "python", "aws"] for a in apps) else 0))
            maintenance_level = MaintenanceLevel.LOW if complexity_score < 3 else MaintenanceLevel.MEDIUM
            monthly_opex = 10.0 + (len(action_apps) - 1) * 5.0

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
