from sqlalchemy import Column, String, Integer, Float, JSON, Enum as SQLEnum
from .database import Base
from .schema import MaintenanceLevel
import uuid

class AutomationTemplateModel(Base):
    __tablename__ = "automation_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    url = Column(String, nullable=False)
    source_platform = Column(String, nullable=False)
    trigger_app = Column(String, nullable=False)
    action_apps = Column(JSON, nullable=False)
    complexity_score = Column(Integer, nullable=False)
    maintenance_level = Column(SQLEnum(MaintenanceLevel), nullable=False)
    monthly_opex = Column(Float, nullable=False)
    raw_data = Column(JSON)
