from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any, Union
from heuristic_engine import MaintenanceLevel

class AutomationTemplate(BaseModel):
    id: Union[UUID, str] = Field(default_factory=uuid4)
    source_platform: str
    title: str
    description: str
    source_url: str
    trigger_app: str
    action_apps: List[str]
    complexity_score: int = Field(..., ge=1, le=5)
    maintenance_level: MaintenanceLevel
    monthly_opex: float
    raw_data: Dict[str, Any] = Field(default_factory=dict)
