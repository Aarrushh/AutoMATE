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

class PipelineCleaner:
    def __init__(self):
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        self.clean_templates = []

    def rescue_from_logs(self):
        """Uses regex to rescue data from old output*.txt files."""
        for log_file in ["backend/output.txt", "backend/output_v2.txt"]:
            if not os.path.exists(log_file): continue
            logger.info(f"Rescuing from {log_file}...")
            try:
                with open(log_file, 'r', errors='ignore') as f:
                    content = f.read()
                    # Look for { "name": "...", "tools": [...] } patterns
                    matches = re.findall(r'\{"name":.*?"url":".*?"\}', content)
                    for m in matches:
                        try:
                            data = json.loads(m)
                            self.process_single(data, "legacy_log")
                        except: pass
            except: pass

    def process_single(self, t, source):
        try:
            name = t.get('name') or t.get('title')
            if not name: return
            apps = t.get('tools') or t.get('apps', [])
            action_apps = [a.get('name') if isinstance(a, dict) else str(a) for a in apps]

            template = AutomationTemplate(
                source_platform=source,
                name=name,
                description=t.get('description', name),
                action_apps=action_apps,
                url=t.get('url')
            )
            self.clean_templates.append(template)
        except: pass

    def process_raw_data(self):
        if not os.path.exists(RAW_DATA_DIR): return
        for fname in os.listdir(RAW_DATA_DIR):
            if not fname.endswith('.json'): continue
            with open(os.path.join(RAW_DATA_DIR, fname), 'r') as f:
                try:
                    data = json.load(f)
                    source = fname.split('_')[0]
                    # Handle Next.js data vs API vs Synthetic
                    if 'props' in data: # Next.js
                        items = data.get('props', {}).get('pageProps', {}).get('templates', [])
                    else:
                        items = data if isinstance(data, list) else data.get('data', [])

                    for item in items:
                        self.process_single(item, source)
                except: pass

    def run_cleaner(self):
        self.rescue_from_logs()
        self.process_raw_data()

        # Deduplicate
        seen = set()
        final = []
        for t in self.clean_templates:
            uid = t.url or (t.name + t.source_platform)
            if uid not in seen:
                final.append(t.model_dump())
                seen.add(uid)

        with open(CLEAN_TEMPLATES_FILE, 'w') as f:
            json.dump(final, f, indent=2, default=str)
        logger.info(f"Saved {len(final)} clean templates.")

if __name__ == "__main__":
    cleaner = PipelineCleaner()
    cleaner.run_cleaner()
