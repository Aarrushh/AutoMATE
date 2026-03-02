import json
import logging
import os
import re
from uuid import uuid4
from pydantic import ValidationError
from backend.schema import AutomationTemplate

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DATA_DIR = "backend/raw_data"
PROCESSED_DATA_DIR = "backend/processed_data"
CLEAN_TEMPLATES_FILE = os.path.join(PROCESSED_DATA_DIR, "clean_templates.json")
FAILED_PARSE_LOG = "backend/failed_parse.log"

class PipelineCleaner:
    def __init__(self):
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        self.clean_templates = []
        self.failed_log = open(FAILED_PARSE_LOG, "a")

    def log_failure(self, message):
        self.failed_log.write(f"{message}\n")

    def rescue_data_from_txt(self, filename):
        logger.info(f"Rescuing data from {filename}...")
        try:
            with open(filename, 'r', encoding='utf-16' if 'output' in filename else 'utf-8') as f:
                content = f.read()
                # Simple regex rescue for Zapier-like logs
                # Looks for "Processing Category: {category}" and "Progress: {count} templates scraped"
                # or just name/description lines.
                # In reality, the output.txt seems to be logs.
                # Let's try to find template entries if they were logged.

                # Looking for patterns like: "template = { ... }"
                # Since the original scraper logged progress, maybe it didn't log the full template data.
                # However, templates_zapier.json IS structured.
                pass
        except Exception as e:
            logger.error(f"Error rescuing from {filename}: {e}")

    def process_zapier_raw(self, data):
        # Extract from __NEXT_DATA__ structure
        # Simplified example:
        try:
            props = data.get('props', {}).get('pageProps', {})
            templates_data = props.get('templates', []) or props.get('template', [])
            if not isinstance(templates_data, list):
                templates_data = [templates_data] if templates_data else []

            for t in templates_data:
                try:
                    name = t.get('title') or t.get('name')
                    description = t.get('description') or name
                    apps = t.get('apps', [])
                    action_apps = [app.get('name') for app in apps if isinstance(app, dict)]

                    template = AutomationTemplate(
                        source_platform="zapier",
                        name=name,
                        description=description,
                        action_apps=action_apps,
                        url=t.get('url')
                    )
                    self.clean_templates.append(template)
                except Exception as e:
                    self.log_failure(f"Zapier template parse error: {e} | Data: {t}")
        except Exception as e:
            self.log_failure(f"Zapier raw data parse error: {e}")

    def process_make_raw(self, data):
        # Extract from __NEXT_DATA__ or similar
        try:
            props = data.get('props', {}).get('pageProps', {})
            templates_data = props.get('templates', [])
            for t in templates_data:
                try:
                    name = t.get('name')
                    description = t.get('description') or name
                    apps = t.get('apps', [])
                    action_apps = [app.get('name') for app in apps]

                    template = AutomationTemplate(
                        source_platform="make",
                        name=name,
                        description=description,
                        action_apps=action_apps,
                        url=f"https://www.make.com/en/templates/details/{t.get('slug')}"
                    )
                    self.clean_templates.append(template)
                except Exception as e:
                    self.log_failure(f"Make.com template parse error: {e} | Data: {t}")
        except Exception as e:
            self.log_failure(f"Make.com raw data parse error: {e}")

    def process_legacy_json(self):
        legacy_file = "backend/templates_zapier.json"
        if os.path.exists(legacy_file):
            logger.info(f"Processing legacy file {legacy_file}...")
            try:
                with open(legacy_file, 'r') as f:
                    data = json.load(f)
                    templates = data.get('data', [])
                    for t in templates:
                        try:
                            # Map legacy to new schema
                            template = AutomationTemplate(
                                source_platform="zapier",
                                name=t.get('name'),
                                description=t.get('description'),
                                action_apps=t.get('tools', []),
                                url=t.get('url'),
                                category=t.get('category')
                            )
                            self.clean_templates.append(template)
                        except Exception as e:
                            self.log_failure(f"Legacy JSON template parse error: {e} | Data: {t}")
            except Exception as e:
                logger.error(f"Error processing legacy JSON: {e}")

    def run_cleaner(self):
        # Process legacy files
        self.process_legacy_json()

        # Process rescued data (skeleton)
        for log_file in ["backend/output.txt", "backend/output_v2.txt"]:
            if os.path.exists(log_file):
                self.rescue_data_from_txt(log_file)

        # Process raw_data/
        for filename in os.listdir(RAW_DATA_DIR):
            filepath = os.path.join(RAW_DATA_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    if filename.endswith('.json'):
                        data = json.load(f)
                        if 'zapier' in filename:
                            self.process_zapier_raw(data)
                        elif 'make' in filename:
                            self.process_make_raw(data)
                    # Add logic for n8n/github HTML files if needed
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

        # Save cleaned data
        unique_templates = {str(t.id): t.model_dump() for t in self.clean_templates}
        # Actually deduplicate by URL if present, or name
        final_list = []
        seen_identifiers = set()
        for t in self.clean_templates:
            identifier = t.url or (t.name + t.source_platform)
            if identifier not in seen_identifiers:
                final_list.append(t.model_dump())
                seen_identifiers.add(identifier)

        with open(CLEAN_TEMPLATES_FILE, 'w') as f:
            json.dump(final_list, f, indent=2, default=str)

        logger.info(f"Saved {len(final_list)} clean templates to {CLEAN_TEMPLATES_FILE}")
        self.failed_log.close()

if __name__ == "__main__":
    cleaner = PipelineCleaner()
    cleaner.run_cleaner()
