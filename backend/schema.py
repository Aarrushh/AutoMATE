from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID, uuid4

class MaintenanceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AutomationTemplate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    source_url: str
    source_platform: str = "Zapier"
    trigger_app: str
    action_apps: List[str]
    complexity_score: int = Field(ge=1, le=5)
    maintenance_level: MaintenanceLevel
    monthly_opex: float
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Send Slack messages for new Trello cards",
                "description": "Whenever a new card is added to a Trello list, a message is sent to a Slack channel.",
                "source_url": "https://zapier.com/templates/details/123",
                "source_platform": "Zapier",
                "trigger_app": "Trello",
                "action_apps": ["Slack"],
                "complexity_score": 1,
                "maintenance_level": "LOW",
                "monthly_opex": 0.0,
                "raw_data": {}
            }
        }
