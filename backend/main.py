from fastapi import FastAPI
from .graph_builder import GraphBuilder

app = FastAPI()
graph_builder = GraphBuilder()

@app.get("/")
def read_root():
    return {"message": "Automation Engine is Online"}

@app.get("/search")
def search_automation(query: str):
    # This is a dummy response to test the connection
    return {
        "user_query": query,
        "recommendation": "Zapier: Connect Gmail to Sheets",
        "feasibility_score": 95
    }

@app.get("/api/graph/full")
def get_full_graph():
    return graph_builder.get_full_graph()

@app.get("/api/graph/recommendations/{app_name}")
def get_recommendations(app_name: str):
    return graph_builder.get_recommendations(app_name)
