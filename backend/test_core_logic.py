import pytest
import uuid
from pydantic import ValidationError
from unittest.mock import MagicMock, patch

# We import from backend.schema, backend.heuristic_engine, etc.
# These files might not exist yet, which is part of the task.
try:
    from backend.schema import AutomationTemplate, MaintenanceLevel
    from backend.heuristic_engine import HeuristicEngine
    from backend.llm_cleaner import LLMNormalizer, AppCache
except ImportError:
    # Fallback for when running within the backend directory during testing
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from schema import AutomationTemplate, MaintenanceLevel
    from heuristic_engine import HeuristicEngine
    from llm_cleaner import LLMNormalizer, AppCache

# --- Schema Tests ---

def test_automation_template_validation():
    # Valid data
    valid_data = {
        "id": uuid.uuid4(),
        "name": "Test Template",
        "description": "A test description",
        "url": "https://zapier.com/details/123",
        "source_platform": "Zapier",
        "trigger_app": "Gmail",
        "action_apps": ["Slack"],
        "complexity_score": 3,
        "maintenance_level": MaintenanceLevel.LOW,
        "monthly_opex": 10.0,
        "raw_data": {}
    }
    template = AutomationTemplate(**valid_data)
    assert template.name == "Test Template"
    assert template.action_apps == ["Slack"]

def test_automation_template_invalid_data():
    # Missing required field
    with pytest.raises(ValidationError):
        AutomationTemplate(name="Incomplete")

    # Invalid complexity score (assuming 1-5 range)
    with pytest.raises(ValidationError):
        AutomationTemplate(
            id=uuid.uuid4(),
            name="Bad Score",
            description="...",
            url="http://example.com",
            source_platform="Zapier",
            trigger_app="Gmail",
            action_apps=["Slack"],
            complexity_score=10, # Out of range
            maintenance_level=MaintenanceLevel.LOW,
            monthly_opex=10.0,
            raw_data={}
        )

def test_automation_template_default_actions():
    # Test validator for action_apps
    data = {
        "id": uuid.uuid4(),
        "name": "Empty Actions",
        "description": "...",
        "url": "http://example.com",
        "source_platform": "Zapier",
        "trigger_app": "Gmail",
        "action_apps": [], # Empty list
        "complexity_score": 1,
        "maintenance_level": MaintenanceLevel.LOW,
        "monthly_opex": 0.0,
        "raw_data": {}
    }
    template = AutomationTemplate(**data)
    assert template.action_apps == ["Unknown Action"]

# --- Heuristic Engine Tests ---

def test_calculate_complexity():
    engine = HeuristicEngine()

    # Base case: 1 trigger + 1 action = 2 apps. (2+1)//2 = 1.
    assert engine.calculate_complexity("Gmail", ["Slack"]) == 1

    # 4 apps total. (4+1)//2 = 2.
    assert engine.calculate_complexity("Gmail", ["Slack", "Sheets", "Trello"]) == 2

    # Penalty case: 1 trigger + 1 action (AWS). (2+1)//2 = 1 + 1 (penalty) = 2.
    assert engine.calculate_complexity("Gmail", ["AWS"]) == 2

    # Max cap: many apps
    actions = ["Slack"] * 10
    assert engine.calculate_complexity("Gmail", actions) <= 5

def test_estimate_opex():
    engine = HeuristicEngine()

    # Zapier base: $10.00
    assert engine.estimate_opex("Zapier", "Gmail", ["Slack"]) == 10.0

    # Zapier with extra action: $10 + $5 = $15
    assert engine.estimate_opex("Zapier", "Gmail", ["Slack", "Sheets"]) == 15.0

    # Premium app penalty: Salesforce (+ $15.0)
    # 1 action: $10 (base) + $15 (premium) = $25
    assert engine.estimate_opex("Zapier", "Gmail", ["Salesforce"]) == 25.0

    # n8n flat: $0.24
    assert engine.estimate_opex("n8n", "Gmail", ["Slack"]) == 0.24

# --- LLM Cleaner Mock Test ---

@patch("backend.llm_cleaner.litellm.completion")
def test_llm_normalizer_caching(mock_completion):
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"trigger_app": "Gmail", "action_apps": ["Slack"]}'))
    ]
    mock_completion.return_value = mock_response

    cache = AppCache(":memory:") # Use in-memory DB for test
    normalizer = LLMNormalizer(cache=cache)

    # First call - should hit LLM
    result1 = normalizer.normalize("gmail.v2", ["slack-app-v1"])
    assert result1["trigger_app"] == "Gmail"
    assert mock_completion.call_count == 1

    # Second call - should hit cache
    result2 = normalizer.normalize("gmail.v2", ["slack-app-v1"])
    assert result2["trigger_app"] == "Gmail"
    assert mock_completion.call_count == 1 # Still 1
