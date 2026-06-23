"""Tests for the Todo FastAPI backend."""
import os
import sys

# Make the backend package importable when running from the backend dir
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import pytest
from fastapi.testclient import TestClient

# Use a fresh, isolated DB for the test session BEFORE importing the app
TEST_DB_PATH = os.path.join(BACKEND_DIR, "test_todo.db")
import config  # noqa: E402

config.DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

# Now import app + models (they will use the overridden DATABASE_URL)
import models  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Reset the SQLite database before each test for full isolation."""
    # Drop all and recreate
    models.Base.metadata.drop_all(bind=models.engine)
    models.Base.metadata.create_all(bind=models.engine)
    yield
    # Best-effort cleanup
    models.Base.metadata.drop_all(bind=models.engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, username: str, password: str = "hunter2") -> str:
    res = client.post("/api/register", json={"username": username, "password": password})
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------- Auth ----------------

def test_register_returns_token(client):
    res = client.post("/api/register", json={"username": "alice", "password": "pw123"})
    assert res.status_code == 201
    body = res.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_register_duplicate_username_400(client):
    _register(client, "bob")
    res = client.post("/api/register", json={"username": "bob", "password": "pw123"})
    assert res.status_code == 400
    assert res.json()["detail"] == "Username already exists"


def test_login_success(client):
    _register(client, "carol", "secret")
    res = client.post("/api/login", json={"username": "carol", "password": "secret"})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert isinstance(res.json()["access_token"], str) and res.json()["access_token"]


def test_login_wrong_password_401(client):
    _register(client, "dave", "right")
    res = client.post("/api/login", json={"username": "dave", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


def test_login_unknown_user_401(client):
    res = client.post("/api/login", json={"username": "ghost", "password": "x"})
    assert res.status_code == 401


# ---------------- Todo CRUD ----------------

def test_create_todo(client):
    token = _register(client, "erin")
    res = client.post(
        "/api/todos",
        json={"title": "Buy milk", "description": "Whole milk"},
        headers=_auth(token),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["id"] >= 1
    assert body["title"] == "Buy milk"
    assert body["description"] == "Whole milk"
    assert body["completed"] is False
    assert isinstance(body["created_at"], str) and "T" in body["created_at"]


def test_create_todo_without_description(client):
    token = _register(client, "frank")
    res = client.post(
        "/api/todos",
        json={"title": "Just a title"},
        headers=_auth(token),
    )
    assert res.status_code == 201
    assert res.json()["description"] is None


def test_list_todos_scoped_to_user(client):
    t1 = _register(client, "gina")
    t2 = _register(client, "hank")
    client.post("/api/todos", json={"title": "G1"}, headers=_auth(t1))
    client.post("/api/todos", json={"title": "G2"}, headers=_auth(t1))
    client.post("/api/todos", json={"title": "H1"}, headers=_auth(t2))

    g_list = client.get("/api/todos", headers=_auth(t1)).json()
    h_list = client.get("/api/todos", headers=_auth(t2)).json()

    assert sorted([x["title"] for x in g_list]) == ["G1", "G2"]
    assert [x["title"] for x in h_list] == ["H1"]


def test_update_todo(client):
    token = _register(client, "ivy")
    created = client.post(
        "/api/todos",
        json={"title": "old", "description": "d1"},
        headers=_auth(token),
    ).json()
    res = client.put(
        f"/api/todos/{created['id']}",
        json={"title": "new", "description": "d2"},
        headers=_auth(token),
    )
    assert res.status_code == 200
    assert res.json()["title"] == "new"
    assert res.json()["description"] == "d2"


def test_toggle_todo(client):
    token = _register(client, "jack")
    created = client.post(
        "/api/todos", json={"title": "to-toggle"}, headers=_auth(token)
    ).json()
    assert created["completed"] is False
    res = client.patch(f"/api/todos/{created['id']}/toggle", headers=_auth(token))
    assert res.status_code == 200
    assert res.json()["completed"] is True
    res2 = client.patch(f"/api/todos/{created['id']}/toggle", headers=_auth(token))
    assert res2.json()["completed"] is False


def test_delete_todo(client):
    token = _register(client, "kara")
    created = client.post(
        "/api/todos", json={"title": "to-delete"}, headers=_auth(token)
    ).json()
    res = client.delete(f"/api/todos/{created['id']}", headers=_auth(token))
    assert res.status_code == 200
    assert res.json()["detail"] == "Todo deleted"
    # Now it's gone
    listed = client.get("/api/todos", headers=_auth(token)).json()
    assert listed == []


# ---------------- Authorization & isolation ----------------

def test_unauthorized_list_todos_401(client):
    res = client.get("/api/todos")
    assert res.status_code == 401


def test_unauthorized_create_todo_401(client):
    res = client.post("/api/todos", json={"title": "x"})
    assert res.status_code == 401


def test_invalid_token_401(client):
    res = client.get("/api/todos", headers=_auth("not-a-jwt"))
    assert res.status_code == 401


def test_cannot_access_other_users_todo(client):
    t_alice = _register(client, "alice2")
    t_bob = _register(client, "bob2")
    created = client.post(
        "/api/todos", json={"title": "alice's todo"}, headers=_auth(t_alice)
    ).json()

    # Bob cannot see, update, toggle, or delete Alice's todo
    assert client.get("/api/todos", headers=_auth(t_bob)).json() == []
    assert client.put(
        f"/api/todos/{created['id']}",
        json={"title": "hijack"},
        headers=_auth(t_bob),
    ).status_code == 404
    assert client.patch(
        f"/api/todos/{created['id']}/toggle", headers=_auth(t_bob)
    ).status_code == 404
    assert client.delete(
        f"/api/todos/{created['id']}", headers=_auth(t_bob)
    ).status_code == 404


def test_health_smoke(client):
    # The app should at minimum have a CORS preflight pathway; basic sanity
    res = client.get("/openapi.json")
    assert res.status_code == 200
