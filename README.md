# Antigravity IDE Local Execution Instructions

To run the full 10,000 URL scrape locally on your machine, please follow the steps below carefully. Ensure you are in the root directory of the repository.

### Setup and Execution

1. `pip install -r backend/requirements.txt`
2. `playwright install`
3. `python backend/main_etl.py` (Wait for database to populate)
4. `python backend/export_neo4j.py`
5. `python backend/export_jsonl.py`

*Note: Do not run `main_etl.py` or the exporters in cloud sandboxes as they will time out.*
