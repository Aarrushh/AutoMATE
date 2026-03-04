from enum import Enum
from typing import List, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field

class MaintenanceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AutomationTemplate(BaseModel):
    id: Union[UUID, str]
    title: str
    description: str
    source_url: str
    trigger_app: str
    action_apps: List[str]
    complexity_score: int = Field(..., ge=1, le=5)
    maintenance_level: MaintenanceLevel
    monthly_opex: float
    raw_data: Dict[str, Any]
