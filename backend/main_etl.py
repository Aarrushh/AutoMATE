import asyncio
import logging
from typing import List, Dict, Any
from backend.scraper import ZapierScraper
from backend.make_scraper import MakeScraper
from backend.llm_cleaner import LLMNormalizer, AppCache
from backend.heuristic_engine import HeuristicEngine
from backend.schema import AutomationTemplate
from backend.vector_store import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedScraper:
    def __init__(self):
        self.zapier = ZapierScraper()
        self.make = MakeScraper()

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        if "zapier.com" in url:
            return await self.zapier.scrape_url(url)
        elif "make.com" in url:
            return await self.make.scrape_url(url)
        else:
            raise ValueError(f"Unsupported platform for URL: {url}")

class ETLPipeline:
    def __init__(self):
        self.scraper = UnifiedScraper()
        self.cleaner = LLMNormalizer()
        self.heuristic_engine = HeuristicEngine()
        self.embedder = EmbeddingService()

    async def process_url(self, url: str):
        logger.info(f"Processing URL: {url}")

        # 1. Scrape
        raw_data = await self.scraper.scrape_url(url)

        # 2. Clean
        clean_names = await self.cleaner.normalize_async(
            raw_data["raw_apps"][0] if raw_data["raw_apps"] else "Unknown",
            raw_data["raw_apps"][1:] if len(raw_data["raw_apps"]) > 1 else []
        )

        # 3. Score
        metrics = self.heuristic_engine.get_all_metrics(
            raw_data["source"],
            clean_names["trigger_app"],
            clean_names["action_apps"]
        )

        # 4. Model
        template = AutomationTemplate(
            name=raw_data["title"],
            description=raw_data["description"],
            url=url,
            source_platform=raw_data["source"],
            trigger_app=clean_names["trigger_app"],
            action_apps=clean_names["action_apps"],
            complexity_score=metrics["complexity_score"],
            maintenance_level=metrics["maintenance_level"],
            monthly_opex=metrics["monthly_opex"],
            raw_data=raw_data
        )

        # 5. Persist (Mocked here for now, or just return)
        # 6. Embed & Vector Store
        # metadata = self.embedder.prepare_metadata(template)
        # self.embedder.upsert_templates([template])

        return template

if __name__ == "__main__":
    pipeline = ETLPipeline()
    # To be used with CLI orchestrator
