import json
import os
from collections import defaultdict

class GraphBuilder:
    def __init__(self, data_path="backend/templates_zapier.json"):
        self.data_path = data_path
        self.nodes = set()
        self.edges = defaultdict(int) # (source, target) -> weight
        self.load_data()

    def load_data(self):
        if not os.path.exists(self.data_path):
            return

        try:
            with open(self.data_path, "r") as f:
                content = json.load(f)
                templates = content.get("data", [])
                for template in templates:
                    tools = template.get("tools", [])
                    if not tools:
                        continue

                    # Add all tools as nodes
                    for tool in tools:
                        self.nodes.add(tool)

                    # Heuristic: first tool is trigger, rest are actions
                    if len(tools) >= 2:
                        trigger = tools[0]
                        actions = tools[1:]
                        for action in actions:
                            self.edges[(trigger, action)] += 1
        except Exception as e:
            print(f"Error loading data: {e}")

    def get_full_graph(self):
        nodes_list = [{"id": node} for node in sorted(list(self.nodes))]
        links_list = [
            {"source": source, "target": target, "weight": weight}
            for (source, target), weight in self.edges.items()
        ]
        return {"nodes": nodes_list, "links": links_list}

    def get_recommendations(self, app_name):
        # Find all edges where app_name is the source (trigger)
        recommendations = []
        for (source, target), weight in self.edges.items():
            if source.lower() == app_name.lower():
                recommendations.append({"app": target, "weight": weight})

        # Sort by weight descending and take top 5
        recommendations.sort(key=lambda x: x["weight"], reverse=True)
        return recommendations[:5]
