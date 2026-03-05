from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from .database import get_db, engine, Base
from .models import DBAutomationTemplate
from .schema import AutomationTemplate
from .embedder import EmbeddingService
from .vector_store import VectorStore
from .graph_service import GraphBuilder

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Automation Engine API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
embedding_service = EmbeddingService()
vector_store = VectorStore()
graph_builder = GraphBuilder()

@app.get("/")
def read_root():
    return {"message": "Automation Engine is Online"}

@app.get("/api/templates", response_model=List[AutomationTemplate])
def get_templates(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    templates = db.query(DBAutomationTemplate).offset(skip).limit(limit).all()
    return templates

@app.get("/api/search", response_model=List[AutomationTemplate])
def search_templates(
    query: str,
    max_opex: Optional[float] = None,
    max_complexity: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # 1. Vectorize query
    vector = embedding_service.get_embedding(query)

    # 2. Search in VectorStore
    filter_dict = {}
    if max_opex is not None:
        filter_dict["monthly_opex"] = {"$lte": max_opex}
    if max_complexity is not None:
        filter_dict["complexity_score"] = {"$lte": max_complexity}

    ids = vector_store.search(vector, filter_dict=filter_dict)

    # 3. Retrieve from SQL
    templates = db.query(DBAutomationTemplate).filter(DBAutomationTemplate.id.in_(ids)).all()

    # Also apply filters at DB level for safety
    if max_opex is not None:
        templates = [t for t in templates if t.monthly_opex <= max_opex]
    if max_complexity is not None:
        templates = [t for t in templates if t.complexity_score <= max_complexity]

    return templates

@app.get("/api/graph/full")
def get_full_graph(db: Session = Depends(get_db)):
    return graph_builder.build_adjacency_list(db)

@app.get("/api/graph/recommendations/{app_name}")
def get_recommendations(app_name: str, db: Session = Depends(get_db)):
    recommendations = graph_builder.get_recommendations(db, app_name)
    return recommendations
