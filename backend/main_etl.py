import asyncio
import csv
import logging
import os
import sys
from typing import List, Optional
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from .scraper import ZapierScraper
from .make_scraper import MakeScraper
from .llm_cleaner import LLMNormalizer
from .heuristic_engine import HeuristicEngine
from .schema import AutomationTemplate
from .models import AutomationTemplateModel
from .database import SessionLocal, engine, Base

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl_pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ETLPipeline")

class ETLPipeline:
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self.zapier_scraper = ZapierScraper()
        self.make_scraper = MakeScraper()
        self.normalizer = LLMNormalizer()
        self.heuristic_engine = HeuristicEngine()

        # Initialize database
        Base.metadata.create_all(bind=engine)

    async def process_url(self, browser_context, url: str):
        async with self.semaphore:
            logger.info(f"Starting processing for URL: {url}")
            page = await browser_context.new_page()
            try:
                # 1. Route to correct scraper
                domain = urlparse(url).netloc
                raw_record = None

                if "zapier.com" in domain:
                    raw_record = await self.zapier_scraper.scrape_url(page, url)
                elif "make.com" in domain:
                    raw_record = await self.make_scraper.scrape_url(page, url)
                else:
                    logger.warning(f"Unsupported domain for URL: {url}")
                    return

                if not raw_record:
                    logger.error(f"Failed to scrape URL: {url}")
                    return

                # 2. Normalize App Names
                try:
                    normalized = self.normalizer.clean_apps(
                        raw_record["trigger_app"],
                        raw_record["action_apps"]
                    )
                    raw_record["trigger_app"] = normalized.trigger_app
                    raw_record["action_apps"] = normalized.action_apps
                except Exception as e:
                    logger.warning(f"Normalization failed for {url}, using raw names: {e}")

                # 3. Recalculate Metrics
                raw_record["complexity_score"] = self.heuristic_engine.calculate_complexity(
                    raw_record["trigger_app"], raw_record["action_apps"]
                )
                raw_record["maintenance_level"] = self.heuristic_engine.determine_maintenance(
                    raw_record["complexity_score"]
                )
                raw_record["monthly_opex"] = self.heuristic_engine.estimate_opex(
                    raw_record["trigger_app"], raw_record["action_apps"]
                )

                # 4. Validate with Pydantic
                validated_template = AutomationTemplate(**raw_record)

                # 5. Save to Database
                self.save_to_db(validated_template)
                logger.info(f"Successfully processed and saved: {url}")

            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}", exc_info=True)
            finally:
                await page.close()

    def save_to_db(self, template: AutomationTemplate):
        db = SessionLocal()
        try:
            db_item = AutomationTemplateModel(
                id=str(template.id),
                source_platform=template.source_platform,
                name=template.name,
                description=template.description,
                trigger_app=template.trigger_app,
                action_apps=template.action_apps,
                complexity_score=template.complexity_score,
                maintenance_level=template.maintenance_level.value,
                monthly_opex=template.monthly_opex,
                url=template.url,
                category=template.category
            )
            db.merge(db_item) # merge handles update if ID exists
            db.commit()
        except Exception as e:
            logger.error(f"Database save error: {e}")
            db.rollback()
        finally:
            db.close()

    async def run(self, urls: List[str]):
        logger.info(f"Starting ETL pipeline for {len(urls)} URLs")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            tasks = [self.process_url(context, url) for url in urls]
            await asyncio.gather(*tasks)

            await browser.close()
        logger.info("ETL pipeline execution completed.")

def load_urls_from_csv(file_path: str) -> List[str]:
    urls = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                urls.append(row[0])
    return urls

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Master ETL Pipeline")
    parser.add_argument("--urls", nargs="+", help="List of template URLs to process")
    parser.add_argument("--csv", help="Path to CSV file containing URLs")
    args = parser.parse_args()

    urls = []
    if args.urls:
        urls.extend(args.urls)
    if args.csv:
        urls.extend(load_urls_from_csv(args.csv))

    if not urls:
        logger.error("No URLs provided. Use --urls or --csv.")
        return

    pipeline = ETLPipeline(max_workers=5)
    await pipeline.run(urls)

if __name__ == "__main__":
    asyncio.run(main())
