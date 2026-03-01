from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Automation Engine is Online"}

@app.get("/search")
def search_automation(query: str = Query(..., max_length=100)):
    # This is a dummy response to test the connection
    return {
        "user_query": query,
        "recommendation": "Zapier: Connect Gmail to Sheets",
        "feasibility_score": 95
    }
