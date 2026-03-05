import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import Base, get_db
from backend.models import AutomationTemplateModel
from backend.schema import MaintenanceLevel
import uuid

# --- Setup Mock Database ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# --- Mock Data and Services ---
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Add dummy templates
    for i in range(15):
        template = AutomationTemplateModel(
            id=str(uuid.uuid4()),
            source_platform="Zapier",
            name=f"Template {i}",
            description=f"Description {i}",
            trigger_app="Gmail",
            action_apps=["Google Sheets"],
            complexity_score=2,
            maintenance_level=MaintenanceLevel.LOW,
            monthly_opex=10.0 * i,
            url=f"http://example.com/{i}"
        )
        db.add(template)
    db.commit()
    yield
    db.close()
    Base.metadata.drop_all(bind=engine)

class MockVectorStore:
    def search(self, query_vector, max_opex=None, max_complexity=None):
        # Mock logic: return a few IDs from the DB
        db = TestingSessionLocal()
        query = db.query(AutomationTemplateModel)
        if max_opex is not None:
            query = query.filter(AutomationTemplateModel.monthly_opex <= max_opex)
        if max_complexity is not None:
            query = query.filter(AutomationTemplateModel.complexity_score <= max_complexity)
        ids = [t.id for t in query.limit(5).all()]
        db.close()
        return ids

class MockEmbeddingService:
    def get_embedding(self, text):
        return [0.1] * 384

class MockGraphBuilder:
    def get_full_graph(self):
        return {
            "nodes": [{"id": "Gmail", "type": "app"}, {"id": "Sheets", "type": "app"}],
            "links": [{"source": "Gmail", "target": "Sheets", "type": "USES_ACTION"}]
        }

# Inject Mocks into main app
import backend.main as main_mod
main_mod.vector_store = MockVectorStore()
main_mod.embedder = MockEmbeddingService()
main_mod.graph_builder = MockGraphBuilder()

client = TestClient(app)

# --- Tests ---

def test_get_templates_pagination():
    # Test first page
    response = client.get("/api/templates?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert data[0]["name"] == "Template 0"

    # Test second page
    response = client.get("/api/templates?skip=10&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5 # Total 15 records
    assert data[0]["name"] == "Template 10"

def test_api_search_with_params():
    # Test search with max_opex filter
    response = client.get("/api/search?query=test&max_opex=50")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for template in data:
        assert template["monthly_opex"] <= 50

def test_get_graph_full_format():
    response = client.get("/api/graph/full")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "links" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["links"], list)
    assert len(data["nodes"]) == 2
    assert data["links"][0]["source"] == "Gmail"
