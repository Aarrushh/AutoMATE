from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List

class TechSpecs(BaseModel):
    trigger_app: str
    action_apps: List[str]

class CostMetrics(BaseModel):
    estimated_cost: float

class AutomationTemplate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    platform_source: str
    description: str
    tech_specs: TechSpecs
    financials: CostMetrics
