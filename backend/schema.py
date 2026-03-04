from enum import Enum
from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class MaintenanceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AutomationTemplate(BaseModel):
    id: UUID
    title: str
    description: str
    source_url: str
    source_platform: str
    trigger_app: str
    action_apps: List[str] = Field(default_factory=list)
    complexity_score: int = Field(ge=1, le=5)
    maintenance_level: MaintenanceLevel
    monthly_opex: float
    raw_data: Dict[str, Any]

    @field_validator("action_apps", mode="before")
    @classmethod
    def default_action_apps(cls, v):
        if v is None or (isinstance(v, list) and len(v) == 0):
            return ["Unknown Action"]
        return v
