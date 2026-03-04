import asyncio
import json
import logging
import random
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

from scraper_base import BaseScraper
from heuristic_engine import HeuristicEngine
from schema import AutomationTemplate

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MakeScraper(BaseScraper):
    """
    Scraper for Make.com templates.
    Inherits from BaseScraper for robust browser management and stealth.
    """
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)

    async def scrape_template_detail(self, url: str) -> Optional[AutomationTemplate]:
        """
        Scrapes a Make.com template detail page and returns a validated AutomationTemplate.
        """
        if not self.browser:
            await self.start()

        context = await self._create_context()
        page = await context.new_page()
        await self._stealth.apply_stealth_async(page)

        try:
            logger.info(f"Navigating to {url}")
            # Navigate with a generous timeout and wait for network idle
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Specific handling for Make's dynamic rendering
            # We wait for key elements that indicate the page has rendered its main content.
            try:
                # Wait for any of these: a canvas (common in scenario builders),
                # a template name, or a general data-test-id.
                await page.wait_for_selector('h1, canvas, [data-test-id="template-name"], [data-test-id="canvas"]', timeout=20000)
            except Exception as e:
                logger.warning(f"Timeout waiting for specific Make.com elements on {url}: {e}")

            # Human-like delay
            await asyncio.sleep(random.uniform(2, 4))

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # 1. Extract Template Title
            title = "Unknown Title"
            title_el = soup.find('h1') or soup.select_one('[data-test-id="template-name"]') or soup.select_one('.template-title')
            if title_el:
                title = title_el.get_text(strip=True)

            # 2. Extract Template Description
            description = ""
            desc_el = soup.select_one('[data-test-id="template-description"]') or soup.select_one('.template-description') or soup.select_one('.description')
            if desc_el:
                description = desc_el.get_text(strip=True)

            # 3. Analyze the Make.com module list
            # Identify the Trigger App and Action Apps
            apps = []

            # Try to find module names via data-test-id first (more robust)
            module_name_elements = await page.query_selector_all('[data-test-id="module-name"]')
            for el in module_name_elements:
                name = await el.inner_text()
                if name and name.strip() not in apps:
                    apps.append(name.strip())

            # Fallback to parsing icons with alt text in common module containers
            if not apps:
                # Make.com templates often list apps with their icons
                module_icons = soup.select('.template-icons img[alt], .scenario-modules img[alt], [data-test-id="module"] img[alt], .apps-list img[alt]')
                for icon in module_icons:
                    alt = icon.get('alt')
                    if alt and alt not in apps:
                        # Filter out common non-app alt texts
                        if alt.lower() not in ['make', 'trigger', 'action', 'module']:
                            apps.append(alt)

            # Last effort: look for any image alt text that might be an app in the main area
            if not apps:
                main_content = soup.find('main') or soup.body
                if main_content:
                    for img in main_content.select('img[alt]'):
                        alt = img.get('alt')
                        if alt and len(alt) > 2 and alt not in apps:
                            # Heuristic: app names usually don't have certain words
                            if not any(word in alt.lower() for word in ['banner', 'logo', 'background', 'icon']):
                                apps.append(alt)

            if not apps:
                apps = ["Unknown App"]

            # Identify Trigger and Action Apps
            # By convention in Make.com templates, the first module is the trigger.
            trigger_app = apps[0]
            action_apps = apps[1:] if len(apps) > 1 else []

            # 4. Pass into HeuristicEngine for metrics
            complexity_score = HeuristicEngine.calculate_complexity(trigger_app, action_apps)
            maintenance_level = HeuristicEngine.determine_maintenance(complexity_score)
            monthly_opex = HeuristicEngine.estimate_opex(trigger_app, action_apps)

            # 5. Output validated AutomationTemplate
            template = AutomationTemplate(
                id=str(json.dumps(url)), # Use URL as a seed for ID or just let it generate one
                source_platform="Make.com",
                title=title,
                description=description,
                source_url=url,
                trigger_app=trigger_app,
                action_apps=action_apps,
                complexity_score=complexity_score,
                maintenance_level=maintenance_level,
                monthly_opex=monthly_opex,
                raw_data={"scraped_url": url, "app_count": len(apps)}
            )
            # Re-generate a proper UUID if needed, but AutomationTemplate handles it

            return template

        except Exception as e:
            logger.error(f"Failed to scrape Make.com template detail {url}: {e}")
            return None
        finally:
            await page.close()
            await context.close()

if __name__ == "__main__":
    # Quick CLI test
    import sys

    async def run_test(url: str):
        async with MakeScraper(headless=True) as scraper:
            template = await scraper.scrape_template_detail(url)
            if template:
                print(template.model_dump_json(indent=2))
            else:
                print("Failed to scrape template.")

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = "https://www.make.com/en/templates/4538-save-new-typeform-responses-to-a-google-sheets-spreadsheet"

    asyncio.run(run_test(test_url))
