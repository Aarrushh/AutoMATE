import csv
from collections import defaultdict
from backend.database import SessionLocal
from backend.models import AutomationTemplateModel

def export_neo4j():
    db = SessionLocal()
    try:
        templates = db.query(AutomationTemplateModel).all()

        apps = set()
        edges = defaultdict(lambda: {"weight": 0, "total_complexity": 0, "total_opex": 0})

        for template in templates:
            trigger = template.trigger_app
            actions = template.action_apps

            apps.add(trigger)
            for action in actions:
                apps.add(action)

                edge_key = (trigger, action)
                edges[edge_key]["weight"] += 1
                edges[edge_key]["total_complexity"] += template.complexity_score
                edges[edge_key]["total_opex"] += template.monthly_opex

        # Write nodes.csv
        with open("nodes.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["app_name:ID", "name", ":LABEL"])
            for app in sorted(list(apps)):
                writer.writerow([app, app, "App"])

        # Write edges.csv
        with open("edges.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([":START_ID", ":END_ID", "weight", "avg_complexity", "avg_opex", ":TYPE"])
            for (start, end), metrics in edges.items():
                weight = metrics["weight"]
                avg_complexity = metrics["total_complexity"] / weight
                avg_opex = metrics["total_opex"] / weight
                writer.writerow([start, end, weight, avg_complexity, avg_opex, "CONNECTS_TO"])

        print(f"Exported {len(apps)} nodes and {len(edges)} edges to CSV.")

    finally:
        db.close()

if __name__ == "__main__":
    export_neo4j()
