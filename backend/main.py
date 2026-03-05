from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import get_db, engine, Base
from .models import AutomationTemplateModel
from .embedder import EmbeddingService
from .vector_store import VectorStore
from .schema import AutomationTemplate

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
embedder = EmbeddingService()
vector_store = VectorStore()

@app.get("/")
def read_root():
    return {"message": "Automation Engine is Online"}

@app.get("/search")
def search_automation(query: str):
    # This is a legacy dummy response to test the connection
    return {
        "user_query": query,
        "recommendation": "Zapier: Connect Gmail to Sheets",
        "feasibility_score": 95
    }

@app.get("/api/search", response_model=List[AutomationTemplate])
def ai_search(
    query: str,
    max_opex: Optional[float] = Query(None),
    max_complexity: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    # 1. Convert natural language query to embedding
    query_embedding = embedder.get_embedding(query)

    # 2. Find best templates in Vector DB (Pinecone mock)
    template_ids = vector_store.search(
        query_vector=query_embedding,
        max_opex=max_opex,
        max_complexity=max_complexity
    )

    # 3. Fetch full template data from SQL DB
    query_db = db.query(AutomationTemplateModel).filter(AutomationTemplateModel.id.in_(template_ids))

    # Re-apply filters in SQL DB as well to ensure correctness (since vector store search is currently mocked)
    if max_opex is not None:
        query_db = query_db.filter(AutomationTemplateModel.monthly_opex <= max_opex)
    if max_complexity is not None:
        query_db = query_db.filter(AutomationTemplateModel.complexity_score <= max_complexity)

    templates = query_db.all()

    # If no templates found in DB (due to mock IDs), return empty list or some mock data if needed for testing
    # For now, let's return what we found
    return templates
