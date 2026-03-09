from enum import Enum
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

class MaintenanceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AutomationTemplate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    url: str
    source_platform: str
    trigger_app: str
    action_apps: List[str] = Field(default_factory=list)
    complexity_score: int = Field(ge=1, le=5)
    maintenance_level: MaintenanceLevel
    monthly_opex: float
    raw_data: Dict = Field(default_factory=dict)

    @field_validator('action_apps', mode='before')
    @classmethod
    def validate_action_apps(cls, v):
        if not v:
            return ["Unknown Action"]
        return v
