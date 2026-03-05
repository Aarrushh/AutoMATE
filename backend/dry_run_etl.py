import asyncio
import logging
from unittest.mock import MagicMock, patch
from backend.main_etl import run_pipeline
from backend.schema import AutomationTemplate, MaintenanceLevel
from backend.database import engine
from backend.models import Base

# Setup logging
logging.basicConfig(level=logging.INFO)

async def mock_scrape_url(url):
    return AutomationTemplate(
        name=f"Mock Template for {url}",
        description="Mock Description",
        url=url,
        source_platform="MockPlatform",
        trigger_app="MockTrigger",
        action_apps=["MockAction1", "MockAction2"],
        complexity_score=2,
        maintenance_level=MaintenanceLevel.LOW,
        monthly_opex=10.0,
        raw_data={}
    )

async def dry_run():
    # Create tables in the local sqlite db for testing
    Base.metadata.create_all(bind=engine)

    urls = [
        "https://zapier.com/templates/details/mock-1",
        "https://www.make.com/en/templates/mock-2"
    ]

    print("Starting dry run with mock scrapers...")

    with patch("backend.scraper.ZapierScraper.scrape_url", side_effect=mock_scrape_url):
        with patch("backend.make_scraper.MakeScraper.scrape_url", side_effect=mock_scrape_url):
            with patch("backend.scraper_base.BaseScraper.start", return_value=None):
                with patch("backend.scraper_base.BaseScraper.stop", return_value=None):
                    await run_pipeline(urls)

    print("Dry run complete. Check automation.db for results.")

if __name__ == "__main__":
    asyncio.run(dry_run())
