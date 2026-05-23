"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_login_returns_token() -> None:
    resp = client.post("/api/auth/login", json={
        "username": "admin", "password": "etfcompass123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_bad_password() -> None:
    resp = client.post("/api/auth/login", json={
        "username": "admin", "password": "wrong",
    })
    assert resp.status_code == 401


def test_dashboard_decision() -> None:
    resp = client.get("/api/dashboard/decision")
    assert resp.status_code == 200


def test_dashboard_diagnostic() -> None:
    resp = client.get("/api/dashboard/diagnostic")
    assert resp.status_code == 200


def test_dashboard_evidence() -> None:
    resp = client.get("/api/dashboard/evidence")
    assert resp.status_code == 200


def test_positions_list() -> None:
    resp = client.get("/api/positions")
    assert resp.status_code == 200


def test_admin_requires_auth() -> None:
    resp = client.get("/api/admin/strategy-params")
    assert resp.status_code == 401


def test_admin_with_auth() -> None:
    login_resp = client.post("/api/auth/login", json={
        "username": "admin", "password": "etfcompass123",
    })
    token = login_resp.json()["access_token"]
    resp = client.get(
        "/api/admin/strategy-params",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_wiki_home() -> None:
    resp = client.get("/wiki/")
    assert resp.status_code == 200


def test_wiki_etf_page() -> None:
    resp = client.get("/wiki/etfs/NIFTYIETF")
    assert resp.status_code == 200
    assert "NIFTYIETF" in resp.text
