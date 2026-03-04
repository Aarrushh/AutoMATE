from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4
from typing import List, Optional

class CostMetrics(BaseModel):
    monthly_opex: float = 0.0

class TechSpecs(BaseModel):
    complexity_score: int = 1
    maintenance_level: str = "Low"

class AutomationTemplate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_platform: str
    name: str
    description: Optional[str] = ""
    trigger_app: Optional[str] = "Unknown"
    action_apps: List[str] = Field(default_factory=list)
    complexity_score: int = 1
    maintenance_level: str = "Low"
    monthly_opex: float = 0.0
    url: Optional[str] = None
    category: Optional[str] = None

    @validator('action_apps', pre=True, always=True)
    def ensure_actions_not_empty(cls, v):
        if not v:
            return ['Unknown Action']
        return v
