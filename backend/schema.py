from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional

class CostMetrics(BaseModel):
    setup_cost: float = 0.0
    estimated_monthly_opex: float
    pricing_model: str = "Subscription"

class AutomationTemplate(BaseModel):
    id: UUID
    source_platform: str
    name: str
    description: str
    trigger_app: str
    action_apps: List[str]
    url: str
    category: str
    cost_metrics: Optional[CostMetrics] = None
