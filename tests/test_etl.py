import unittest
import os
import json
from pathlib import Path
from backend.schema import AutomationTemplate, CostMetrics, TechSpecs
from backend.pipeline_cleaner import estimate_cost

class TestAutoMatchETL(unittest.TestCase):
    def test_schema_validation(self):
        data = {
            "name": "Test Template",
            "description": "A test description",
            "source_platform": "Zapier",
            "trigger_app": "Slack",
            "action_apps": ["Trello"],
            "estimated_cost": 15.0
        }
        template = AutomationTemplate(**data)
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.trigger_app, "Slack")
        self.assertEqual(len(template.action_apps), 1)

    def test_schema_with_metrics_and_specs(self):
        """
        Verify that AutomationTemplate correctly validates new CostMetrics and TechSpecs fields.
        """
        data = {
            "name": "Advanced Automation",
            "description": "A complex workflow",
            "source_platform": "Make",
            "cost_metrics": {
                "monthly_cost": 25.5,
                "currency": "EUR"
            },
            "tech_specs": {
                "complexity": "High",
                "tool_count": 5
            }
        }
        template = AutomationTemplate(**data)

        # Assertions
        self.assertIsInstance(template.cost_metrics, CostMetrics)
        self.assertEqual(template.cost_metrics.monthly_cost, 25.5)
        self.assertEqual(template.cost_metrics.currency, "EUR")

        self.assertIsInstance(template.tech_specs, TechSpecs)
        self.assertEqual(template.tech_specs.complexity, "High")
        self.assertEqual(template.tech_specs.tool_count, 5)

    def test_estimate_cost(self):
        template = {"action_apps": ["Tool1", "Tool2"]}
        cost = estimate_cost(template)
        # 10 + 2*5 = 20
        self.assertEqual(cost, 20.0)

        template_no_actions = {"action_apps": []}
        cost_no_actions = estimate_cost(template_no_actions)
        self.assertEqual(cost_no_actions, 10.0)

    def test_processed_data_exists(self):
        # Create a dummy processed file if it doesn't exist for testing environment
        processed_file = Path("data/processed_templates.json")
        if not processed_file.exists():
            os.makedirs("data", exist_ok=True)
            with open(processed_file, "w") as f:
                json.dump([{"id": "test-id", "source_platform": "Zapier"}], f)

        self.assertTrue(processed_file.exists())
        with open(processed_file, "r") as f:
            data = json.load(f)
            self.assertGreater(len(data), 0)
            self.assertIn("id", data[0])
            self.assertIn("source_platform", data[0])

if __name__ == "__main__":
    unittest.main()
