import unittest
import os
import json
from pathlib import Path
from backend.schema import AutomationTemplate
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

    def test_estimate_cost(self):
        template = {"action_apps": ["Tool1", "Tool2"]}
        cost = estimate_cost(template)
        # 10 + 2*5 = 20
        self.assertEqual(cost, 20.0)

        template_no_actions = {"action_apps": []}
        cost_no_actions = estimate_cost(template_no_actions)
        self.assertEqual(cost_no_actions, 10.0)

    def test_processed_data_exists(self):
        processed_file = Path("data/processed_templates.json")
        self.assertTrue(processed_file.exists())
        with open(processed_file, "r") as f:
            data = json.load(f)
            self.assertGreater(len(data), 0)
            self.assertIn("id", data[0])
            self.assertIn("source_platform", data[0])

if __name__ == "__main__":
    unittest.main()
