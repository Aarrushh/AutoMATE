import os
import shutil
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI

# Import our pipeline scripts
from backend.scraper import run_scraper
from backend.pipeline_cleaner import run_cleaner
from backend.pipeline_embedder import run_embedder
from backend.pipeline_graph import run_graph_prep

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoMatch Backend API")

def clean_house():
    """
    Utility function to move raw data files into backend/raw_data/
    """
    raw_dir = Path("backend/raw_data")
    raw_dir.mkdir(exist_ok=True)

    files_to_move = [
        "backend/output.txt",
        "backend/output_utf8.txt",
        "backend/output_v2.txt",
        "backend/error_log.txt",
        "backend/templates_zapier.json"
    ]

    for file_path in files_to_move:
        p = Path(file_path)
        if p.exists():
            logger.info(f"Moving {file_path} to {raw_dir}")
            try:
                shutil.move(str(p), str(raw_dir / p.name))
            except Exception as e:
                logger.error(f"Failed to move {file_path}: {e}")

async def run_pipeline():
    """
    Orchestrates the full ETL pipeline.
    """
    logger.info("--- Starting AutoMatch ETL Pipeline ---")

    # Step 1: Run Scraper
    logger.info("Step 1: Running Scraper...")
    await run_scraper()

    # Step 2: Run Cleaner
    logger.info("Step 2: Running Data Cleaner...")
    run_cleaner()

    # Step 3: Run Embedder
    logger.info("Step 3: Running Vector Embedder...")
    run_embedder()

    # Step 4: Run Graph Prep
    logger.info("Step 4: Running Graph Data Extraction...")
    run_graph_prep()

    # Clean House
    logger.info("Final Step: Cleaning the house...")
    clean_house()

    logger.info("--- ETL Pipeline Completed Successfully ---")

@app.on_event("startup")
async def startup_event():
    # In production, you might not want to run the full pipeline on every startup
    # but for this architecting task, we ensure it's available.
    pass

@app.get("/")
def read_root():
    return {"message": "AutoMatch AI Automation Consultant API is Online"}

@app.post("/run-pipeline")
async def trigger_pipeline():
    # This endpoint allows manual triggering of the ETL pipeline
    asyncio.create_task(run_pipeline())
    return {"message": "ETL Pipeline started in the background."}

if __name__ == "__main__":
    # If running manually via python backend/main.py, run the pipeline
    asyncio.run(run_pipeline())
