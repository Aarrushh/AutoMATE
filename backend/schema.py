from pydantic import BaseModel, Field
from typing import List, Literal

class TechSpecs(BaseModel):
    trigger_app: str
    action_apps: List[str]
    implementation_complexity: int = Field(..., ge=1, le=5)
    maintenance_cost_level: Literal['Low', 'Medium', 'High']
