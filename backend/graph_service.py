from sqlalchemy.orm import Session
from .models import AutomationTemplateModel
from collections import defaultdict

class GraphBuilder:
    def build_adjacency_list(self, db: Session):
        """
        Queries all templates from the database and builds a directional relationship graph.
        Returns data formatted for frontend visualization (nodes and links).
        """
        templates = db.query(AutomationTemplateModel).all()

        edges = defaultdict(int)
        nodes_set = set()

        for template in templates:
            trigger = template.trigger_app
            actions = template.action_apps

            if not trigger:
                continue

            nodes_set.add(trigger)

            if actions and isinstance(actions, list):
                for action in actions:
                    if action:
                        nodes_set.add(action)
                        # Create a directional relationship: Trigger -> Action
                        edges[(trigger, action)] += 1
            elif actions and isinstance(actions, str):
                # Fallback if actions is stored as a comma-separated string
                action_list = [a.strip() for a in actions.split(",") if a.strip()]
                for action in action_list:
                    nodes_set.add(action)
                    edges[(trigger, action)] += 1

        # Format for frontend visualization
        nodes = [{"id": node} for node in sorted(list(nodes_set))]
        links = [
            {"source": source, "target": target, "weight": weight}
            for (source, target), weight in edges.items()
        ]

        return {
            "nodes": nodes,
            "links": links
        }
