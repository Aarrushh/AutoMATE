import json
import logging
from pathlib import Path
from slugify import slugify

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
PROCESSED_FILE = Path("data/processed_templates.json")
NODES_FILE = Path("data/graph_nodes.json")
EDGES_FILE = Path("data/graph_edges.json")

def run_graph_prep():
    """
    ETL Step 4: Extract Nodes and Edges for Neo4j.
    """
    if not PROCESSED_FILE.exists():
        logger.error(f"Processed file not found: {PROCESSED_FILE}")
        return

    logger.info(f"Loading processed templates from {PROCESSED_FILE}")
    with open(PROCESSED_FILE, "r") as f:
        templates = json.load(f)

    nodes = []
    edges = []
    unique_apps = {} # name -> slug

    # Extract unique apps and template nodes
    for t in templates:
        # Create Template Node
        template_node = {
            "label": "Template",
            "id": t["id"],
            "name": t["name"],
            "source": t["source_platform"],
            "estimated_cost": t.get("estimated_cost")
        }
        nodes.append(template_node)

        # Handle Trigger App
        trigger = t.get("trigger_app")
        if trigger and trigger != "Unknown":
            trigger_slug = slugify(trigger)
            if trigger_slug not in unique_apps:
                unique_apps[trigger_slug] = trigger

            # Edge: Template -> Trigger App
            edges.append({
                "source": t["id"],
                "target": trigger_slug,
                "type": "HAS_TRIGGER"
            })

        # Handle Action Apps
        actions = t.get("action_apps", [])
        for action in actions:
            if action and action != "Unknown":
                action_slug = slugify(action)
                if action_slug not in unique_apps:
                    unique_apps[action_slug] = action

                # Edge: Template -> Action App
                edges.append({
                    "source": t["id"],
                    "target": action_slug,
                    "type": "USES_ACTION"
                })

    # Add App nodes to nodes list
    for slug, name in unique_apps.items():
        nodes.append({
            "label": "App",
            "id": slug,
            "name": name
        })

    # Save outputs
    with open(NODES_FILE, "w") as f:
        json.dump(nodes, f, indent=2)

    with open(EDGES_FILE, "w") as f:
        json.dump(edges, f, indent=2)

    logger.info(f"Successfully extracted {len(nodes)} nodes and {len(edges)} edges.")
    logger.info(f"Saved to {NODES_FILE} and {EDGES_FILE}")

if __name__ == "__main__":
    run_graph_prep()
