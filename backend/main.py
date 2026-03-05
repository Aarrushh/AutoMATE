from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .database import get_db
from .models import DBAutomationTemplate
from .schema import AutomationTemplate

app = FastAPI(title="Automation Engine API")

# CORS middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Automation Engine is Online"}

@app.get("/api/templates", response_model=List[AutomationTemplate])
def get_templates(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Fetch automation templates with pagination.
    """
    templates = db.query(DBAutomationTemplate).offset(skip).limit(limit).all()
    return templates

@app.get("/search")
def search_automation(query: str):
    # This is a dummy response to test the connection
    return {
        "user_query": query,
        "recommendation": "Zapier: Connect Gmail to Sheets",
        "feasibility_score": 95
    }
