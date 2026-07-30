from fastapi.testclient import TestClient
from app import app


def test_health_endpoint():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_root_endpoint():
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "running"


def test_execute_and_replay_flow():
    client = TestClient(app)
    payload = {"task": "Audit payments service for security vulnerabilities"}
    
    res = client.post("/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert "workflow" in data
    assert "id" in data["workflow"]
    assert len(data["events"]) > 0

    workflow_id = data["workflow"]["id"]
    replay_res = client.get(f"/replay/{workflow_id}")
    assert replay_res.status_code == 200
    replay_data = replay_res.json()
    assert replay_data["workflow_id"] == workflow_id
    assert len(replay_data["steps"]) == len(data["events"])


if __name__ == "__main__":
    test_health_endpoint()
    test_root_endpoint()
    test_execute_and_replay_flow()
    print("All API tests PASSED!")
