from sqlalchemy import Column, Integer, String, Float
from .database import Base

class DBAutomationTemplate(Base):
    __tablename__ = "automation_templates"

    id = Column(Integer, primary_key=True, index=True)
    trigger_app = Column(String, index=True)
    action_apps = Column(String)  # Stored as comma-separated values
    complexity_score = Column(Integer)
    monthly_opex = Column(Float)
    maintenance_level = Column(String)
