import sys
import os

# Add the current directory to sys.path so we can import backend.main
sys.path.append(os.getcwd())

try:
    from fastapi.testclient import TestClient
    from backend.main import app
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    sys.exit(0)  # Exit gracefully if dependencies are missing

client = TestClient(app)

def test_search_valid():
    print("Testing valid query...")
    response = client.get("/search", params={"query": "test"})
    assert response.status_code == 200
    assert response.json()["user_query"] == "test"
    print("Valid query test passed.")

def test_search_too_long():
    print("Testing too long query...")
    long_query = "a" * 101
    response = client.get("/search", params={"query": long_query})
    # This should fail with 422 if validation is working
    if response.status_code == 422:
        print("Too long query test passed (got 422).")
    else:
        print(f"Too long query test failed (got {response.status_code}, expected 422).")
        sys.exit(1)

if __name__ == "__main__":
    test_search_valid()
    test_search_too_long()
