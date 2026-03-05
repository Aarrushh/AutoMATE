import asyncio
import logging
from typing import List, Dict
from backend.scraper import ZapierScraper
from backend.make_scraper import MakeScraper
from backend.schema import AutomationTemplate
from backend.database import SessionLocal
from backend.models import AutomationTemplateModel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_url(url: str, scrapers: Dict, semaphore: asyncio.Semaphore) -> AutomationTemplate:
    async with semaphore:
        scraper = None
        if "zapier.com" in url:
            scraper = scrapers["zapier"]
        elif "make.com" in url:
            scraper = scrapers["make"]

        if not scraper:
            logger.warning(f"No scraper found for URL: {url}")
            return None

        try:
            template = await scraper.scrape_url(url)
            return template
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return None

def save_to_db(template: AutomationTemplate):
    if not template:
        return

    db = SessionLocal()
    try:
        # Try to find existing by URL first because merge might try INSERT if ID is different
        existing = db.query(AutomationTemplateModel).filter(AutomationTemplateModel.url == template.url).first()

        if existing:
            # Update existing
            existing.name = template.name
            existing.description = template.description
            existing.trigger_app = template.trigger_app
            existing.action_apps = template.action_apps
            existing.complexity_score = template.complexity_score
            existing.maintenance_level = template.maintenance_level.value
            existing.monthly_opex = template.monthly_opex
            existing.raw_data = template.raw_data
            logger.info(f"Updated in DB: {template.name}")
        else:
            # Insert new
            model = AutomationTemplateModel(
                id=str(template.id),
                name=template.name,
                description=template.description,
                url=template.url,
                source_platform=template.source_platform,
                trigger_app=template.trigger_app,
                action_apps=template.action_apps,
                complexity_score=template.complexity_score,
                maintenance_level=template.maintenance_level.value,
                monthly_opex=template.monthly_opex,
                raw_data=template.raw_data
            )
            db.add(model)
            logger.info(f"Saved to DB: {template.name}")

        db.commit()
    except Exception as e:
        logger.error(f"Failed to save to DB: {e}")
        db.rollback()
    finally:
        db.close()

async def run_pipeline(urls: List[str]):
    # Initialize scrapers once
    scrapers = {
        "zapier": ZapierScraper(),
        "make": MakeScraper()
    }

    # Start browser for each scraper
    await asyncio.gather(*(s.start() for s in scrapers.values()))

    semaphore = asyncio.Semaphore(5)
    tasks = [process_url(url, scrapers, semaphore) for url in urls]

    results = await asyncio.gather(*tasks)

    for template in results:
        if template:
            save_to_db(template)

    # Cleanup browsers
    await asyncio.gather(*(s.stop() for s in scrapers.values()))

if __name__ == "__main__":
    sample_urls = [
        "https://zapier.com/templates/details/123/google-sheets-to-slack",
        "https://www.make.com/en/templates/456-google-sheets-to-slack"
    ]
    asyncio.run(run_pipeline(sample_urls))
