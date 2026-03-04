from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Optional, Union

class CostMetrics(BaseModel):
    """
    Model for cost-related metadata of an automation.
    """
    monthly_cost: float = 0.0
    currency: str = "USD"

class TechSpecs(BaseModel):
    """
    Model for technical specifications of an automation.
    """
    complexity: str = "Low"
    tool_count: int = 0

class AutomationTemplate(BaseModel):
    """
    Pydantic model representing a standardized automation template.
    """
    id: UUID = Field(default_factory=uuid4)
    source_platform: str = "Unknown"
    name: str
    description: str
    trigger_app: Optional[str] = "Unknown"
    action_apps: List[str] = Field(default_factory=list)
    estimated_cost: Optional[Union[float, str]] = None
    cost_metrics: Optional[CostMetrics] = None
    tech_specs: Optional[TechSpecs] = None

    class Config:
        json_schema_extra = {
            "example": {
                "source_platform": "Zapier",
                "name": "Slack to Trello",
                "description": "Create a Trello card for new Slack messages.",
                "trigger_app": "Slack",
                "action_apps": ["Trello"],
                "estimated_cost": 15.0,
                "cost_metrics": {
                    "monthly_cost": 15.0,
                    "currency": "USD"
                },
                "tech_specs": {
                    "complexity": "Low",
                    "tool_count": 2
                }
            }
        }
