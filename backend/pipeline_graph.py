import json
import logging
import os
from uuid import uuid4

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CLEAN_TEMPLATES_FILE = "backend/processed_data/clean_templates.json"
GRAPH_DATA_DIR = "backend/graph_data"
NODES_FILE = os.path.join(GRAPH_DATA_DIR, "nodes.json")
EDGES_FILE = os.path.join(GRAPH_DATA_DIR, "edges.json")

class PipelineGraph:
    def __init__(self):
        os.makedirs(GRAPH_DATA_DIR, exist_ok=True)
        self.nodes = []
        self.edges = []
        self.seen_apps = set()

    def process_templates(self):
        if not os.path.exists(CLEAN_TEMPLATES_FILE):
            logger.error(f"{CLEAN_TEMPLATES_FILE} not found. Run cleaner first.")
            return

        with open(CLEAN_TEMPLATES_FILE, 'r') as f:
            templates = json.load(f)

        logger.info(f"Preparing graph data for {len(templates)} templates...")

        for t in templates:
            t_id = t.get('id')
            # Add Template Node
            self.nodes.append({
                "id": t_id,
                "label": "Template",
                "properties": {
                    "name": t.get('name'),
                    "source": t.get('source_platform'),
                    "url": t.get('url') or ""
                }
            })

            # Handle Apps
            apps = t.get('action_apps', [])
            trigger = t.get('trigger_app')
            if trigger:
                apps.append(trigger)

            for app_name in set(apps):
                if not app_name: continue

                app_id = f"app_{app_name.lower().replace(' ', '_')}"
                if app_name not in self.seen_apps:
                    self.nodes.append({
                        "id": app_id,
                        "label": "App",
                        "properties": {
                            "name": app_name
                        }
                    })
                    self.seen_apps.add(app_name)

                # Add Relationship Edge
                self.edges.append({
                    "id": str(uuid4()),
                    "from": t_id,
                    "to": app_id,
                    "label": "HAS_APP"
                })

        # Save Nodes and Edges
        with open(NODES_FILE, 'w') as f:
            json.dump(self.nodes, f, indent=2, default=str)
        with open(EDGES_FILE, 'w') as f:
            json.dump(self.edges, f, indent=2, default=str)

        logger.info(f"Saved {len(self.nodes)} nodes and {len(self.edges)} edges to {GRAPH_DATA_DIR}")

if __name__ == "__main__":
    graph_prep = PipelineGraph()
    graph_prep.process_templates()
    logger.info("Graph Database Prep complete.")
