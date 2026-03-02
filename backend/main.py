import argparse
import asyncio
import logging
import sys
from backend.pipeline_scraper import AsyncScraper
from backend.pipeline_cleaner import PipelineCleaner
from backend.pipeline_embedder import PipelineEmbedder
from backend.pipeline_graph import PipelineGraph

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Automation Engine Data Compiler CLI")
    parser.add_argument("--scrape", action="store_true", help="Run Phase 1: High-Volume Async Scraper")
    parser.add_argument("--clean", action="store_true", help="Run Phase 2: Pydantic Normalization")
    parser.add_argument("--embed", action="store_true", help="Run Phase 3: Local Vectorization")
    parser.add_argument("--graph", action="store_true", help="Run Phase 4: Graph Database Prep")
    parser.add_argument("--all", action="store_true", help="Run all phases sequentially")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)

    if args.scrape or args.all:
        logger.info(">>> Starting Phase 1: Scraping...")
        scraper = AsyncScraper()
        asyncio.run(scraper.run_all())

    if args.clean or args.all:
        logger.info(">>> Starting Phase 2: Cleaning...")
        cleaner = PipelineCleaner()
        cleaner.run_cleaner()

    if args.embed or args.all:
        logger.info(">>> Starting Phase 3: Vectorization...")
        embedder = PipelineEmbedder()
        templates = embedder.load_clean_data()
        if templates:
            embedder.generate_embeddings(templates)

    if args.graph or args.all:
        logger.info(">>> Starting Phase 4: Graph Prep...")
        graph_prep = PipelineGraph()
        graph_prep.process_templates()

    logger.info("Pipeline Execution Finished Successfully.")

if __name__ == "__main__":
    main()
