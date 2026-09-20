from fastapi.testclient import TestClient

from app.main import app
from app.security.jwt import create_access_token, decode_access_token


client = TestClient(app)


def test_jwt_round_trip() -> None:
    token = create_access_token({"sub": "alice@example.com", "user_id": 42})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "alice@example.com"
    assert payload["user_id"] == 42


def test_register_and_login_endpoints() -> None:
    payload = {
        "email": "alice@example.com",
        "password": "Secret123@",
    }

    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 200
    register_data = register_response.json()
    assert register_data["user"]["email"] == "alice@example.com"
    assert "access_token" in register_data

    login_response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "Secret123@"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["user"]["email"] == "alice@example.com"
    assert "access_token" in login_data


def test_token_endpoint_and_invalid_login() -> None:
    payload = {"email": "bob@example.com", "password": "Secret456#"}

    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 200

    token_response = client.post("/auth/token", json=payload)
    assert token_response.status_code == 200
    assert "access_token" in token_response.json()

    bad_login = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "Wrongpass1#"},
    )
    assert bad_login.status_code == 401


def test_auth_rejects_duplicate_and_missing_token() -> None:
    payload = {"email": "charlie@example.com", "password": "Secret789#"}

    first = client.post("/auth/register", json=payload)
    assert first.status_code == 200

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400

    me_without_token = client.get("/auth/me")
    assert me_without_token.status_code == 401


def test_me_accepts_valid_token_and_rejects_bad_token() -> None:
    payload = {"email": "dora@example.com", "password": "Secret000#"}
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "dora@example.com"

    bad_response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert bad_response.status_code == 401


def test_role_based_endpoint_access() -> None:
    user = client.post(
        "/auth/register",
        json={
            "email": "regular-user@example.com",
            "password": "Secret123@",
            "role": "user",
        },
    ).json()
    supervisor = client.post(
        "/auth/register",
        json={
            "email": "regular-supervisor@example.com",
            "password": "Secret123@",
            "role": "supervisor",
        },
    ).json()

    user_headers = {"Authorization": f"Bearer {user['access_token']}"}
    supervisor_headers = {
        "Authorization": f"Bearer {supervisor['access_token']}"
    }

    assert client.get("/products/").status_code == 401
    assert client.get("/sales/").status_code == 401
    assert client.get("/products/", headers=user_headers).status_code == 200
    assert client.get("/sales/", headers=user_headers).status_code == 403
    assert client.post(
        "/chat/",
        json={"message": "What were this month's sales?"},
        headers=user_headers,
    ).status_code == 403
    assert client.get(
        "/sales/report", headers=user_headers).status_code == 403
    assert client.get(
        "/products/", headers=supervisor_headers).status_code == 200
    assert client.get("/sales/", headers=supervisor_headers).status_code == 200
    assert client.get(
        "/sales/report", headers=supervisor_headers).status_code == 200
