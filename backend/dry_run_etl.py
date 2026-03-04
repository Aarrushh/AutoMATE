import asyncio
import argparse
import json
import sys
import os

# Ensure parent directory is in path for absolute imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def dry_run(mock_scrape: bool):
    print(f"--- Starting ETL Dry Run (Mock Scrape: {mock_scrape}) ---")

    # Delayed imports to allow the rest of the system to be built
    try:
        from main_etl import ETLPipeline
        from schema import AutomationTemplate
    except ImportError as e:
        print(f"Error: Could not import core components. Have you implemented them yet? {e}")
        return

    pipeline = ETLPipeline()

    urls = [
        "https://zapier.com/templates/details/123/gmail-to-slack",
        "https://zapier.com/templates/details/456/salesforce-to-google-sheets",
        "https://www.make.com/en/templates/789/post-to-discord",
        "https://www.make.com/en/templates/012/shopify-to-airtable"
    ]

    for url in urls:
        print(f"\n{'='*20}")
        print(f"PROCESSING: {url}")
        print(f"{'='*20}")

        # Step 1: Raw Extraction
        if mock_scrape:
            source = "zapier" if "zapier" in url else "make"
            raw_data = {
                "title": "Mock Template Title",
                "description": "Mock Description for " + url,
                "raw_apps": ["gmail-v2", "slack-app"] if source == "zapier" else ["shopify", "airtable"],
                "source": source
            }
        else:
            print("Action: Performing Real Scrape...")
            raw_data = await pipeline.scraper.scrape_url(url)

        print(f"STEP 1: RAW DATA EXTRACTED\n{json.dumps(raw_data, indent=2)}")

        # Step 2: LLM Normalization
        print("Action: Normalizing via LLM Cleaner...")
        clean_names = await pipeline.cleaner.normalize_async(
            raw_data["raw_apps"][0],
            raw_data["raw_apps"][1:]
        )
        print(f"STEP 2: CLEAN NAMES\n{json.dumps(clean_names, indent=2)}")

        # Step 3: Heuristics
        print("Action: Calculating Heuristics...")
        metrics = pipeline.heuristic_engine.get_all_metrics(
            raw_data["source"],
            clean_names["trigger_app"],
            clean_names["action_apps"]
        )
        print(f"STEP 3: CALCULATED METRICS\n{json.dumps(metrics, indent=2)}")

        # Step 4: Final DB Payload
        print("Action: Formatting Pydantic Model...")
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
        print(f"STEP 4: FINAL DB PAYLOAD\n{template.model_dump_json(indent=2)}")

        # Step 5: Vector Metadata
        print("Action: Preparing Vector Metadata...")
        metadata = pipeline.embedder.prepare_metadata(template)
        print(f"STEP 5: VECTOR METADATA PAYLOAD\n{json.dumps(metadata, indent=2)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock-scrape", action="store_true", help="Use hardcoded HTML strings")
    args = parser.parse_args()

    try:
        asyncio.run(dry_run(args.mock_scrape))
    except KeyboardInterrupt:
        pass
