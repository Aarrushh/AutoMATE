from typing import List, Dict, Any
try:
    from backend.schema import MaintenanceLevel
except ImportError:
    from schema import MaintenanceLevel

class HeuristicEngine:
    def __init__(self):
        self.complex_apps = ['AWS', 'Code', 'Webhooks', 'Python']
        self.premium_apps = ['Salesforce', 'Shopify', 'QuickBooks']

    def calculate_complexity(self, trigger_app: str, action_apps: List[str]) -> int:
        total_apps = 1 + len(action_apps)
        score = (total_apps + 1) // 2

        all_apps = [trigger_app] + action_apps
        for app in all_apps:
            if any(complex_app.lower() in app.lower() for complex_app in self.complex_apps):
                score += 1

        return min(max(score, 1), 5)

    def estimate_opex(self, platform: str, trigger_app: str, action_apps: List[str]) -> float:
        cost = 0.0
        if platform.lower() == "zapier":
            cost = 10.0 + max(0, len(action_apps) - 1) * 5.0
        elif platform.lower() == "n8n":
            cost = 0.24
        elif platform.lower() == "make":
            # Heuristic for Make not explicitly detailed in memory,
            # but let's assume a base cost or use Zapier's as fallback
            cost = 9.0 + max(0, len(action_apps) - 1) * 4.0
        else:
            cost = 5.0 # Generic fallback

        all_apps = [trigger_app] + action_apps
        for app in all_apps:
            if any(premium.lower() in app.lower() for premium in self.premium_apps):
                cost += 15.0

        if len(action_apps) > 3:
            cost += 5.0

        return round(cost, 2)

    def determine_maintenance_level(self, complexity_score: int) -> MaintenanceLevel:
        if complexity_score <= 2:
            return MaintenanceLevel.LOW
        elif complexity_score <= 4:
            return MaintenanceLevel.MEDIUM
        else:
            return MaintenanceLevel.HIGH

    def get_all_metrics(self, platform: str, trigger_app: str, action_apps: List[str]) -> Dict[str, Any]:
        complexity = self.calculate_complexity(trigger_app, action_apps)
        return {
            "complexity_score": complexity,
            "maintenance_level": self.determine_maintenance_level(complexity),
            "monthly_opex": self.estimate_opex(platform, trigger_app, action_apps)
        }
