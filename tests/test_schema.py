import pytest
from backend.schema import AutomationTemplate

def test_automation_template_default_action_apps():
    # Test with empty action_apps
    template = AutomationTemplate(
        source_platform="Zapier",
        name="Test Template",
        action_apps=[]
    )
    assert template.action_apps == ["Unknown Action"]

def test_automation_template_with_action_apps():
    # Test with provided action_apps
    template = AutomationTemplate(
        source_platform="Zapier",
        name="Test Template",
        action_apps=["Slack", "Gmail"]
    )
    assert template.action_apps == ["Slack", "Gmail"]

def test_automation_template_implicit_empty_action_apps():
    # Test when action_apps is not provided at all
    template = AutomationTemplate(
        source_platform="Zapier",
        name="Test Template"
    )
    assert template.action_apps == ["Unknown Action"]
