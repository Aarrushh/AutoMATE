import asyncio
import logging
from backend.main_etl import run_pipeline
from backend.database import engine
from backend.models import Base

# Setup logging
logging.basicConfig(level=logging.INFO)

async def dry_run():
    # Create tables in the local sqlite db for testing
    Base.metadata.create_all(bind=engine)

    urls = [
        "https://zapier.com/apps/google-sheets/integrations/slack",
        "https://www.make.com/en/templates/13014-save-new-typeform-entries-to-a-google-sheets-spreadsheet"
    ]

    print("Starting dry run with real URLs...")

    await run_pipeline(urls)

    print("Dry run complete. Check automation.db for results.")

if __name__ == "__main__":
    asyncio.run(dry_run())
