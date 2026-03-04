import json
import os
import re
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any
from backend.schema import AutomationTemplate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/etl_warnings.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PROCESSED_FILE = DATA_DIR / "processed_templates.json"
RAW_DATA_DIR = Path("backend/raw_data") # This will be used after moving files, but for now we look in backend/

def estimate_cost(template: Dict[str, Any]) -> float:
    """
    Heuristic for estimated_cost: $10 base + $5 per action tool.
    """
    base_cost = 10.0
    action_count = len(template.get("action_apps", []))
    return base_cost + (action_count * 5.0)

def parse_txt_files(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Parses messy log/txt files to find potential template entries.
    Look for lines that might contain template names and descriptions.
    """
    extracted = []
    # Pattern to find potential categories and names in the logs
    # Based on observation, some lines have "Processing Category: ..." or just lists
    for file_path in file_paths:
        if not file_path.exists():
            continue

        logger.info(f"Parsing unstructured file: {file_path}")
        try:
            # Handle potential UTF-16 encoding as seen in exploration
            try:
                content = file_path.read_bytes().decode('utf-16le', errors='ignore')
            except:
                content = file_path.read_text(errors='ignore')

            lines = content.splitlines()
            for line in lines:
                line = line.strip()
                # Skip log-specific lines
                if " - INFO - " in line or " - ERROR - " in line or "At line:" in line or "+" in line:
                    continue

                # Heuristic: If it's a reasonably long line and not a URL, might be a template name or description
                if 10 < len(line) < 200 and not line.startswith("http"):
                    # We'll treat these as "found in logs" templates
                    # Since we don't have triggers/actions for these, they will be "Unknown"
                    extracted.append({
                        "name": line,
                        "description": line,
                        "source_platform": "Log Discovery",
                        "trigger_app": "Unknown",
                        "action_apps": [],
                    })
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")

    return extracted

def run_cleaner():
    """
    ETL Step 2: Clean and validate data from multiple sources.
    """
    all_data = []

    # 1. Load from templates_zapier.json
    zapier_file = Path("backend/templates_zapier.json")
    if zapier_file.exists():
        logger.info(f"Loading data from {zapier_file}")
        try:
            with open(zapier_file, "r") as f:
                zap_content = json.load(f)
                zap_list = zap_content.get("data", [])
                for item in zap_list:
                    # Enrich with source
                    item["source_platform"] = "Zapier"

                    # Split tools into trigger and actions if possible
                    # Heuristic: first is trigger, rest are actions
                    tools = item.get("tools", [])
                    if tools:
                        item["trigger_app"] = tools[0]
                        item["action_apps"] = tools[1:]
                    else:
                        item["trigger_app"] = "Unknown"
                        item["action_apps"] = []

                    all_data.append(item)
        except Exception as e:
            logger.error(f"Error loading {zapier_file}: {e}")

    # 2. Load from unstructured .txt files
    txt_files = [
        Path("backend/output.txt"),
        Path("backend/output_utf8.txt"),
        Path("backend/output_v2.txt")
    ]
    discovered_logs = parse_txt_files(txt_files)
    all_data.extend(discovered_logs)

    # 3. Standardize and Validate with Pydantic
    processed_templates = []
    for raw_item in all_data:
        try:
            # Calculate estimated cost
            raw_item["estimated_cost"] = estimate_cost(raw_item)

            # Validate with schema
            template = AutomationTemplate(**raw_item)
            processed_templates.append(template.model_dump())
        except Exception as e:
            logger.warning(f"Skipping unparseable item: {raw_item.get('name', 'Unknown')}. Error: {e}")
            # The logging handler already writes to etl_warnings.log

    # 4. Save processed data
    # Ensure ID is string for JSON
    for t in processed_templates:
        t["id"] = str(t["id"])

    with open(PROCESSED_FILE, "w") as f:
        json.dump(processed_templates, f, indent=2)

    logger.info(f"Successfully cleaned and saved {len(processed_templates)} templates to {PROCESSED_FILE}")

if __name__ == "__main__":
    run_cleaner()
