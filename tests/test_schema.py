import pytest
from pydantic import ValidationError
from backend.schema import TechSpecs

def test_tech_specs_valid():
    data = {
        "trigger_app": "Gmail",
        "action_apps": ["Google Sheets", "Slack"],
        "implementation_complexity": 3,
        "maintenance_cost_level": "Medium"
    }
    specs = TechSpecs(**data)
    assert specs.trigger_app == "Gmail"
    assert specs.action_apps == ["Google Sheets", "Slack"]
    assert specs.implementation_complexity == 3
    assert specs.maintenance_cost_level == "Medium"

def test_tech_specs_invalid_complexity():
    with pytest.raises(ValidationError):
        TechSpecs(
            trigger_app="Gmail",
            action_apps=["Slack"],
            implementation_complexity=6,
            maintenance_cost_level="Low"
        )
    with pytest.raises(ValidationError):
        TechSpecs(
            trigger_app="Gmail",
            action_apps=["Slack"],
            implementation_complexity=0,
            maintenance_cost_level="Low"
        )

def test_tech_specs_invalid_maintenance_level():
    with pytest.raises(ValidationError):
        TechSpecs(
            trigger_app="Gmail",
            action_apps=["Slack"],
            implementation_complexity=3,
            maintenance_cost_level="Very High"
        )

def test_tech_specs_missing_fields():
    with pytest.raises(ValidationError):
        TechSpecs(
            trigger_app="Gmail"
        )
