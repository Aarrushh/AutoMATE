from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4
from typing import List, Optional

class AutomationTemplate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_platform: str
    name: str
    description: Optional[str] = ""
    trigger_app: Optional[str] = None
    action_apps: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    category: Optional[str] = None

    @validator('action_apps', always=True)
    def ensure_actions_not_empty(cls, v):
        if not v:
            return ['Unknown Action']
        return v
