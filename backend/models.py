from sqlalchemy import Column, String, Integer, Float, JSON, MetaData
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class AutomationTemplateModel(Base):
    __tablename__ = "automation_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    url = Column(String, unique=True, nullable=False)
    source_platform = Column(String, nullable=False)
    trigger_app = Column(String, nullable=False)
    action_apps = Column(JSON, nullable=False)
    complexity_score = Column(Integer)
    maintenance_level = Column(String)
    monthly_opex = Column(Float)
    raw_data = Column(JSON)

    def __repr__(self):
        return f"<AutomationTemplate(name='{self.name}', platform='{self.source_platform}')>"
