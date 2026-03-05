from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID, uuid4

class MaintenanceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AutomationTemplate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    url: str
    source_platform: str
    trigger_app: str
    action_apps: List[str]
    complexity_score: int = Field(ge=1, le=5)
    maintenance_level: MaintenanceLevel
    monthly_opex: float
    raw_data: Optional[Dict[str, Any]] = None

    @field_validator('action_apps', mode='before')
    @classmethod
    def default_action_apps(cls, v):
        if not v:
            return ['Unknown Action']
        return v
