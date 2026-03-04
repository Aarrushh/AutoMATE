from enum import Enum

class MaintenanceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class HeuristicEngine:
    @staticmethod
    def calculate_complexity(trigger_app: str, action_apps: list[str]) -> int:
        """
        Returns a score from 1-5.
        Base it on the total number of apps (1-2 apps = 1, 3-4 = 2, etc.)
        and add a +1 penalty if complex apps like "AWS", "Code", "Webhooks", or "Python" are in the list.
        Max score is 5.
        """
        total_apps = 1 + len(action_apps)
        base_score = (total_apps + 1) // 2

        complex_apps = {"AWS", "Code", "Webhooks", "Python"}
        all_apps = [trigger_app] + action_apps

        penalty = 0
        if any(app in complex_apps for app in all_apps):
            penalty = 1

        score = base_score + penalty
        return min(max(score, 1), 5)

    @staticmethod
    def determine_maintenance(complexity_score: int) -> MaintenanceLevel:
        """
        Returns LOW (score 1-2), MEDIUM (score 3-4), or HIGH (score 5).
        """
        if complexity_score <= 2:
            return MaintenanceLevel.LOW
        elif complexity_score <= 4:
            return MaintenanceLevel.MEDIUM
        else:
            return MaintenanceLevel.HIGH

    @staticmethod
    def estimate_opex(trigger_app: str, action_apps: list[str]) -> float:
        """
        Provide a baseline calculation. Assume $0 for basic apps,
        but add $15.00 for each premium app like "Salesforce", "Shopify", or "QuickBooks".
        Add a base operational cost of $5.00 if there are more than 3 action apps.
        """
        premium_apps = {"Salesforce", "Shopify", "QuickBooks"}
        all_apps = [trigger_app] + action_apps

        opex = 0.0
        for app in all_apps:
            if app in premium_apps:
                opex += 15.0

        if len(action_apps) > 3:
            opex += 5.0

        return opex
