from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Optional, Union

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

    class Config:
        json_schema_extra = {
            "example": {
                "source_platform": "Zapier",
                "name": "Slack to Trello",
                "description": "Create a Trello card for new Slack messages.",
                "trigger_app": "Slack",
                "action_apps": ["Trello"],
                "estimated_cost": 15.0
            }
        }
