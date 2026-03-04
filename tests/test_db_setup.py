import pytest
from uuid import uuid4
from backend.schema import AutomationTemplate
from backend.models import AutomationTemplateModel
from backend.database import Base, engine, SessionLocal
from sqlalchemy.orm import Session
import os

# Setup test database
@pytest.fixture(scope="module")
def db():
    # Use a separate test database file
    test_db_url = "sqlite:///./test_automation.db"
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        if os.path.exists("./test_automation.db"):
            os.remove("./test_automation.db")

def test_pydantic_to_sqlalchemy(db: Session):
    # 1. Create Pydantic model instance
    pydantic_data = AutomationTemplate(
        source_platform="Zapier",
        name="Test Automation",
        description="A test automation description",
        trigger_app="Slack",
        action_apps=["Google Sheets"],
        complexity_score=2,
        maintenance_level="Medium",
        monthly_opex=15.5,
        url="https://zapier.com/test",
        category="productivity"
    )

    # 2. Convert to SQLAlchemy model
    db_model = AutomationTemplateModel(
        id=str(pydantic_data.id),
        source_platform=pydantic_data.source_platform,
        name=pydantic_data.name,
        description=pydantic_data.description,
        trigger_app=pydantic_data.trigger_app,
        action_apps=pydantic_data.action_apps,
        complexity_score=pydantic_data.complexity_score,
        maintenance_level=pydantic_data.maintenance_level,
        monthly_opex=pydantic_data.monthly_opex,
        url=pydantic_data.url,
        category=pydantic_data.category
    )

    # 3. Save to database
    db.add(db_model)
    db.commit()
    db.refresh(db_model)

    # 4. Verify retrieval
    retrieved = db.query(AutomationTemplateModel).filter(AutomationTemplateModel.id == str(pydantic_data.id)).first()
    assert retrieved is not None
    assert retrieved.name == "Test Automation"
    assert retrieved.trigger_app == "Slack"
    assert retrieved.action_apps == ["Google Sheets"]
    assert retrieved.monthly_opex == 15.5

def test_pydantic_validator():
    # Test that action_apps defaults to ['Unknown Action'] if empty
    pydantic_data = AutomationTemplate(
        source_platform="Zapier",
        name="Test Empty Actions",
        action_apps=[]
    )
    assert pydantic_data.action_apps == ['Unknown Action']
