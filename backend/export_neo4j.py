import csv
import os
from collections import defaultdict
try:
    from .database import SessionLocal
    from .models import DBAutomationTemplate
except ImportError:
    from database import SessionLocal
    from models import DBAutomationTemplate

def export_to_neo4j():
    session = SessionLocal()
    try:
        templates = session.query(DBAutomationTemplate).all()

        apps = set()
        edges = defaultdict(lambda: {
            'count': 0,
            'total_complexity': 0,
            'total_opex': 0
        })

        for template in templates:
            trigger = template.trigger_app
            apps.add(trigger)

            actions = template.action_apps
            if isinstance(actions, str):
                import json
                actions = json.loads(actions)

            for action in actions:
                apps.add(action)

                # Create connection from trigger to action
                edge_key = (trigger, action)
                edges[edge_key]['count'] += 1
                edges[edge_key]['total_complexity'] += (template.complexity_score or 0)
                edges[edge_key]['total_opex'] += (template.monthly_opex or 0.0)

        # Generate nodes.csv
        with open('nodes.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['app_name:ID', 'name', ':LABEL'])
            for app in sorted(apps):
                writer.writerow([app, app, 'App'])

        # Generate edges.csv
        with open('edges.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID', ':END_ID', 'weight:int', 'avg_complexity:float', 'avg_opex:float', ':TYPE'])
            for (start, end), metrics in edges.items():
                count = metrics['count']
                avg_complexity = metrics['total_complexity'] / count
                avg_opex = metrics['total_opex'] / count
                writer.writerow([start, end, count, avg_complexity, avg_opex, 'CONNECTS_TO'])

        print(f"Exported {len(apps)} nodes to nodes.csv")
        print(f"Exported {len(edges)} edges to edges.csv")

    finally:
        session.close()

if __name__ == "__main__":
    export_to_neo4j()
