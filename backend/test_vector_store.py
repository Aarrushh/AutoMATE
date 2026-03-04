import uuid
import sys
import os

# Add the current directory to sys.path to allow imports from backend/
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from schema import AutomationTemplate, MaintenanceLevel
    from vector_store import upsert_templates
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_upsert_templates():
    # 1. Create a dummy AutomationTemplate
    template_id = uuid.uuid4()
    template = AutomationTemplate(
        id=template_id,
        title="CRM to Slack",
        description="Notify Slack when a new CRM lead is created",
        source_url="https://example.com/crm-slack",
        source_platform="Zapier",
        trigger_app="Salesforce",
        action_apps=["Slack"],
        complexity_score=2,
        maintenance_level=MaintenanceLevel.LOW,
        monthly_opex=15.5,
        raw_data={"some": "raw data"}
    )

    # 2. Create dummy embedding
    embedding = [0.1, 0.2, 0.3]

    # 3. Call upsert_templates
    payloads = upsert_templates([template], [embedding])

    # 4. Assertions
    assert len(payloads) == 1
    payload = payloads[0]

    assert payload["id"] == str(template_id)
    assert payload["values"] == embedding

    metadata = payload["metadata"]
    assert metadata["trigger_app"] == "Salesforce"
    assert metadata["action_apps"] == ["Slack"]
    assert metadata["complexity_score"] == 2
    assert metadata["maintenance_level"] == "LOW"
    assert metadata["monthly_opex"] == 15.5
    assert metadata["title"] == "CRM to Slack"

    print("Test passed successfully!")

def test_action_apps_validator():
    # Test validator with empty action_apps
    template = AutomationTemplate(
        id=uuid.uuid4(),
        title="Empty Action Apps",
        description="Test description",
        source_url="https://example.com/empty",
        source_platform="Zapier",
        trigger_app="Salesforce",
        action_apps=[],
        complexity_score=1,
        maintenance_level=MaintenanceLevel.LOW,
        monthly_opex=0.0,
        raw_data={}
    )
    assert template.action_apps == ["Unknown Action"]
    print("Validator test passed!")

if __name__ == "__main__":
    try:
        test_upsert_templates()
        test_action_apps_validator()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
