from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import get_db, engine, Base
from .models import AutomationTemplateModel
from .embedder import EmbeddingService
from .vector_store import VectorStore
from .schema import AutomationTemplate
from .graph_builder import GraphBuilder

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Automation Engine API")

# CORS middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embedder = EmbeddingService()
vector_store = VectorStore()
graph_builder = GraphBuilder()

@app.get("/")
def read_root():
    return {"message": "Automation Engine is Online"}

@app.get("/api/templates", response_model=List[AutomationTemplate])
def get_templates(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Fetch automation templates with pagination.
    """
    templates = db.query(AutomationTemplateModel).offset(skip).limit(limit).all()
    return templates

@app.get("/api/search", response_model=List[AutomationTemplate])
def ai_search(
    query: str,
    max_opex: Optional[float] = Query(None),
    max_complexity: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    AI-powered search using vector embeddings and metadata filters.
    """
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
    return templates

@app.get("/api/graph/full")
def get_full_graph():
    """
    Retrieve the full knowledge graph nodes and links.
    """
    return graph_builder.get_full_graph()

@app.get("/search")
def search_automation(query: str = Query(..., max_length=100)):
    # This is a legacy dummy response to test the connection
    return {
        "user_query": query,
        "recommendation": "Zapier: Connect Gmail to Sheets",
        "feasibility_score": 95
    }
