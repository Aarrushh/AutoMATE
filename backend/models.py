from sqlalchemy import Column, Integer, String, JSON
from .database import Base

class AutomationTemplateModel(Base):
    __tablename__ = "automation_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    trigger_app = Column(String)
    action_apps = Column(JSON) # Stores a list of action app names
