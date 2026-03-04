from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator, UUID4
import uuid

class MaintenanceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AutomationTemplate(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    name: str
    description: str
    url: str
    source_platform: str
    trigger_app: str
    action_apps: List[str] = Field(default_factory=list)
    complexity_score: int = Field(ge=1, le=5)
    maintenance_level: MaintenanceLevel
    monthly_opex: float
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    @validator("action_apps", pre=True, always=True)
    def set_default_actions(cls, v):
        if not v:
            return ["Unknown Action"]
        return v
