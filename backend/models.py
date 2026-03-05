from sqlalchemy import Column, String, Integer, Float, JSON
from .database import Base
import uuid

class DBAutomationTemplate(Base):
    __tablename__ = "automation_templates"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String)
    url = Column(String)
    source_platform = Column(String)
    trigger_app = Column(String)
    action_apps = Column(JSON)  # List[str]
    complexity_score = Column(Integer)
    maintenance_level = Column(String)
    monthly_opex = Column(Float)
    raw_data = Column(JSON)
