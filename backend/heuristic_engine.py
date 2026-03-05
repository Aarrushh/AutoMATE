from typing import List

class HeuristicEngine:
    @staticmethod
    def calculate_complexity(trigger_app: str, action_apps: List[str]) -> int:
        total_apps = 1 + len(action_apps)
        base_score = (total_apps + 1) // 2

        complex_apps = {'AWS', 'Code', 'Webhooks', 'Python', 'Javascript'}
        bonus = 0
        all_apps = [trigger_app.lower()] + [a.lower() for a in action_apps]
        for app in all_apps:
            if any(c.lower() in app for c in complex_apps):
                bonus += 1

        return min(5, base_score + bonus)

    @staticmethod
    def estimate_maintenance(complexity_score: int) -> str:
        if complexity_score <= 2:
            return "LOW"
        elif complexity_score <= 4:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def estimate_opex(source_platform: str, action_apps: List[str]) -> float:
        if source_platform.lower() == "zapier":
            base_cost = 20.0
        else: # make.com
            base_cost = 9.0

        premium_apps = {'Salesforce', 'Shopify', 'QuickBooks'}
        additional_cost = 0
        for app in action_apps:
            if any(p.lower() in app.lower() for p in premium_apps):
                additional_cost += 15.0

        if len(action_apps) > 3:
            additional_cost += 5.0

        return base_cost + additional_cost
