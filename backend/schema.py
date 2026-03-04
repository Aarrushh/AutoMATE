from enum import Enum
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, field_validator

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
    action_apps: List[str]
    complexity_score: int
    maintenance_level: MaintenanceLevel
    monthly_opex: float
    raw_data: Dict[str, Any]

    @field_validator('action_apps', mode='before')
    @classmethod
    def default_action_apps(cls, v: Any) -> List[str]:
        if v is None or (isinstance(v, list) and len(v) == 0):
            return ['Unknown Action']
        return v
