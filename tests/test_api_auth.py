"""Integration tests for multi-user authentication and data isolation in API endpoints."""

import pytest
from fastapi.testclient import TestClient
from server import app
from db.connection import get_conn
from db.migrations import run_migrations


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a TestClient with a fresh temporary database."""
    test_db = str(tmp_path / "test_api_tracker.db")
    with get_conn(test_db) as conn:
        run_migrations(conn)

    # Override DB_PATH in db.connection and server
    import db.connection
    monkeypatch.setattr(db.connection, "DB_PATH", test_db)

    with TestClient(app) as test_client:
        yield test_client


def test_health_check_public(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_protected_route_rejects_unauthenticated(client):
    res = client.get("/api/today")
    assert res.status_code == 401


def test_register_login_flow(client):
    # Register
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "password123", "name": "Alice"},
    )
    assert reg_res.status_code == 200
    data = reg_res.json()
    assert "token" in data
    assert data["user"]["email"] == "alice@example.com"
    token = data["token"]

    # Me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Alice"

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login_res.status_code == 200
    assert "token" in login_res.json()


def test_user_data_isolation(client):
    """User B should not see or access User A's tasks or data."""
    # 1. Create Alice
    alice_res = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "password123", "name": "Alice"},
    ).json()
    alice_token = alice_res["token"]

    # Alice creates a task
    t_res = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={"title": "Alice's Secret Task", "priority": "high"},
    )
    assert t_res.status_code == 200
    alice_task_id = t_res.json()["id"]

    # Alice sees her task
    alice_today = client.get("/api/today", headers={"Authorization": f"Bearer {alice_token}"}).json()
    assert any(t["id"] == alice_task_id for t in alice_today["tasks"])

    # 2. Create Bob
    bob_res = client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "password": "password456", "name": "Bob"},
    ).json()
    bob_token = bob_res["token"]

    # Bob's dashboard should be completely clean
    bob_today = client.get("/api/today", headers={"Authorization": f"Bearer {bob_token}"}).json()
    assert len(bob_today["tasks"]) == 0
    assert not any(t["id"] == alice_task_id for t in bob_today["tasks"])

    # Bob cannot complete Alice's task
    bob_complete = client.post(
        f"/api/tasks/{alice_task_id}/complete",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    # Task not found for Bob -> error
    assert bob_complete.status_code == 400
