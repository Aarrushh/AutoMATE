from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import get_db
from backend.models import DBAutomationTemplate, Base
import pytest
import os

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
if os.path.exists("./test_api.db"):
    os.remove("./test_api.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Automation Engine is Online"}

def test_get_templates_empty():
    # Clear DB for this test if needed, but it's first and we deleted the file
    response = client.get("/api/templates")
    assert response.status_code == 200
    assert response.json() == []

def test_get_templates_with_data():
    # Seed data
    db = TestingSessionLocal()
    template = DBAutomationTemplate(
        name="Test Template",
        description="A test description",
        url="http://test.com",
        source_platform="Zapier",
        trigger_app="Gmail",
        action_apps=["Slack"],
        complexity_score=3,
        maintenance_level="MEDIUM",
        monthly_opex=15.0,
        raw_data={}
    )
    db.add(template)
    db.commit()
    db.close()

    response = client.get("/api/templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Template"
    assert data[0]["trigger_app"] == "Gmail"

def test_pagination():
    db = TestingSessionLocal()
    # Add 15 templates
    for i in range(15):
        template = DBAutomationTemplate(
            name=f"Template {i}",
            description=f"Desc {i}",
            url=f"http://test{i}.com",
            source_platform="Zapier",
            trigger_app="Gmail",
            action_apps=["Slack"],
            complexity_score=1,
            maintenance_level="LOW",
            monthly_opex=10.0,
            raw_data={}
        )
        db.add(template)
    db.commit()
    db.close()

    # Default limit is 10
    response = client.get("/api/templates")
    assert len(response.json()) >= 10

    # Custom skip and limit
    response = client.get("/api/templates?skip=10&limit=5")
    assert len(response.json()) == 5
