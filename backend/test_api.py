import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from .database import Base, get_db
from .main import app
from .models import DBAutomationTemplate
from .embedder import EmbeddingService
from .vector_store import VectorStore

# 1. Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Dependency Override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# 3. Mocks
def mock_get_embedding(self, text):
    return [0.1] * 384

def mock_vector_search(self, vector, limit=10, filter_dict=None):
    # For testing, we'll return all seeded IDs
    session = TestingSessionLocal()
    ids = [t.id for t in session.query(DBAutomationTemplate).all()]
    session.close()
    return ids

@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    # Apply mocks
    monkeypatch.setattr(EmbeddingService, "get_embedding", mock_get_embedding)
    monkeypatch.setattr(VectorStore, "search", mock_vector_search)

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed data
    templates = [
        DBAutomationTemplate(
            id=str(uuid.uuid4()),
            name="Gmail to Slack",
            description="Simple integration",
            url="http://example.com/1",
            source_platform="zapier",
            trigger_app="Gmail",
            action_apps=["Slack"],
            complexity_score=1,
            maintenance_level="LOW",
            monthly_opex=20.0,
            raw_data={}
        ),
        DBAutomationTemplate(
            id=str(uuid.uuid4()),
            name="Salesforce to HubSpot to Slack",
            description="Complex integration",
            url="http://example.com/2",
            source_platform="zapier",
            trigger_app="Salesforce",
            action_apps=["HubSpot", "Slack"],
            complexity_score=4,
            maintenance_level="MEDIUM",
            monthly_opex=50.0,
            raw_data={}
        ),
        DBAutomationTemplate(
            id=str(uuid.uuid4()),
            name="Gmail to Google Sheets",
            description="Another Gmail one",
            url="http://example.com/3",
            source_platform="make.com",
            trigger_app="Gmail",
            action_apps=["Google Sheets"],
            complexity_score=2,
            maintenance_level="LOW",
            monthly_opex=9.0,
            raw_data={}
        )
    ]
    db.add_all(templates)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

# 4. Tests
def test_get_templates():
    response = client.get("/api/templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Gmail to Slack"

def test_search():
    # Test with query
    response = client.get("/api/search?query=test")
    assert response.status_code == 200
    assert len(response.json()) == 3

    # Test with max_opex
    response = client.get("/api/search?query=test&max_opex=25.0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2 # Gmail to Slack (20) and Gmail to Sheets (9)

    # Test with max_complexity
    response = client.get("/api/search?query=test&max_complexity=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2 # Gmail to Slack (1) and Gmail to Sheets (2)

def test_graph_full():
    response = client.get("/api/graph/full")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "links" in data
    # Gmail, Slack, Salesforce, HubSpot, Google Sheets = 5 nodes
    assert len(data["nodes"]) == 5

def test_graph_recommendations():
    response = client.get("/api/graph/recommendations/Gmail")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "Slack" in data
    assert "Google Sheets" in data
