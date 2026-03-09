import unittest
from backend.schema import AutomationTemplate, MaintenanceLevel
from backend.models import AutomationTemplateModel
from uuid import uuid4

class TestCoreLogic(unittest.TestCase):
    def test_automation_template_validation(self):
        data = {
            "name": "Test Template",
            "description": "A test description",
            "url": "http://example.com",
            "source_platform": "Zapier",
            "trigger_app": "Gmail",
            "action_apps": ["Slack"],
            "complexity_score": 3,
            "maintenance_level": "MEDIUM",
            "monthly_opex": 15.0
        }
        template = AutomationTemplate(**data)
        self.assertEqual(template.trigger_app, "Gmail")
        self.assertEqual(template.action_apps, ["Slack"])

    def test_empty_action_apps_validator(self):
        data = {
            "name": "Test Template",
            "description": "A test description",
            "url": "http://example.com",
            "source_platform": "Zapier",
            "trigger_app": "Gmail",
            "action_apps": [],
            "complexity_score": 1,
            "maintenance_level": "LOW",
            "monthly_opex": 10.0
        }
        template = AutomationTemplate(**data)
        self.assertEqual(template.action_apps, ["Unknown Action"])

    def test_model_mapping(self):
        template = AutomationTemplate(
            name="Test Template",
            description="A test description",
            url="http://example.com",
            source_platform="Zapier",
            trigger_app="Gmail",
            action_apps=["Slack"],
            complexity_score=3,
            maintenance_level=MaintenanceLevel.MEDIUM,
            monthly_opex=15.0
        )

        model = AutomationTemplateModel(
            id=str(template.id),
            name=template.name,
            description=template.description,
            url=template.url,
            source_platform=template.source_platform,
            trigger_app=template.trigger_app,
            action_apps=template.action_apps,
            complexity_score=template.complexity_score,
            maintenance_level=template.maintenance_level.value,
            monthly_opex=template.monthly_opex,
            raw_data=template.raw_data
        )

        self.assertEqual(model.trigger_app, "Gmail")
        self.assertEqual(model.action_apps, ["Slack"])
        self.assertEqual(model.maintenance_level, "MEDIUM")

if __name__ == "__main__":
    unittest.main()
