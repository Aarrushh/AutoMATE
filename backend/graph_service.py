from sqlalchemy.orm import Session
from .models import DBAutomationTemplate
from collections import defaultdict

class GraphBuilder:
    def build_adjacency_list(self, db: Session):
        templates = db.query(DBAutomationTemplate).all()
        nodes = set()
        links = []

        edge_counts = defaultdict(int)

        for t in templates:
            trigger = t.trigger_app
            nodes.add(trigger)
            for action in t.action_apps:
                nodes.add(action)
                edge_counts[(trigger, action)] += 1

        formatted_nodes = [{"id": node} for node in nodes]
        formatted_links = [
            {"source": source, "target": target, "value": count}
            for (source, target), count in edge_counts.items()
        ]

        return {"nodes": formatted_nodes, "links": formatted_links}

    def get_recommendations(self, db: Session, app_name: str, limit: int = 5):
        templates = db.query(DBAutomationTemplate).filter(
            DBAutomationTemplate.trigger_app.ilike(f"%{app_name}%")
        ).all()

        action_counts = defaultdict(int)
        for t in templates:
            for action in t.action_apps:
                action_counts[action] += 1

        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        return [action for action, count in sorted_actions[:limit]]
