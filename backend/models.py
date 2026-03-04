from sqlalchemy import Column, String, Integer, Float, JSON
from .database import Base

class AutomationTemplateModel(Base):
    __tablename__ = "automation_templates"

    id = Column(String, primary_key=True, index=True)
    source_platform = Column(String, index=True)
    name = Column(String, index=True)
    description = Column(String)
    trigger_app = Column(String)
    action_apps = Column(JSON)
    complexity_score = Column(Integer)
    maintenance_level = Column(String)
    monthly_opex = Column(Float)
    url = Column(String)
    category = Column(String, index=True)
