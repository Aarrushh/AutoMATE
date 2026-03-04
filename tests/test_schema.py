import pytest
from backend.schema import CostMetrics, AutomationTemplate
from uuid import uuid4

def test_cost_metrics_defaults():
    metrics = CostMetrics(estimated_monthly_opex=10.5)
    assert metrics.setup_cost == 0.0
    assert metrics.estimated_monthly_opex == 10.5
    assert metrics.pricing_model == "Subscription"

def test_cost_metrics_custom():
    metrics = CostMetrics(setup_cost=50.0, estimated_monthly_opex=15.0, pricing_model="One-time")
    assert metrics.setup_cost == 50.0
    assert metrics.estimated_monthly_opex == 15.0
    assert metrics.pricing_model == "One-time"

def test_automation_template_minimal():
    template_id = uuid4()
    template = AutomationTemplate(
        id=template_id,
        source_platform="Zapier",
        name="Test Sync",
        description="Syncs data",
        trigger_app="Gmail",
        action_apps=["Google Sheets"],
        url="https://example.com",
        category="productivity"
    )
    assert template.id == template_id
    assert template.cost_metrics is None

def test_automation_template_with_metrics():
    template_id = uuid4()
    metrics = CostMetrics(estimated_monthly_opex=5.0)
    template = AutomationTemplate(
        id=template_id,
        source_platform="Make",
        name="Complex Flow",
        description="Many steps",
        trigger_app="Webhooks",
        action_apps=["Slack", "Airtable"],
        url="https://make.com",
        category="operations",
        cost_metrics=metrics
    )
    assert template.cost_metrics.estimated_monthly_opex == 5.0
