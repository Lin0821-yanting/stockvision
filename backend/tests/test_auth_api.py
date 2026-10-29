"""登入 API：註冊、登入、登出、session 過期、Bearer token、失敗次數限制與需要登入的端點。"""

from datetime import timedelta

import pytest

from app.core.config import get_settings
from app.models.user import UserSession
from tests.conftest import DEFAULT_NOW, PASSWORD, register

PROTECTED = [
    ("get", "/api/watchlist"),
    ("get", "/api/account"),
    ("post", "/api/account/reset"),
    ("get", "/api/portfolio"),
    ("get", "/api/trades"),
    ("get", "/api/alerts"),
    ("get", "/api/notifications"),
]


def test_register_logs_in_and_creates_account(client, db):
    response = register(client, "Alice_01")

    body = response.json()
    assert body["user"]["username"] == "alice_01"  # 帳號一律存小寫
    assert body["user"]["display_name"] == "Alice_01"
    cookie_header = response.headers["set-cookie"].lower()
    assert "httponly" in cookie_header and "samesite=lax" in cookie_header
    assert client.get("/api/auth/me").json()["username"] == "alice_01"
    assert client.get("/api/account").json()["cash"] == 1_000_000
    session = db.query(UserSession).one()
    assert session.token_hash != client.cookies.get("sv_session")  # 資料庫只存雜湊
    assert len(session.token_hash) == 64


def test_username_is_unique_case_insensitively(client):
    register(client, "alice")

    response = client.post("/api/auth/register", json={"username": "ALICE", "password": PASSWORD})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "password": PASSWORD},
        {"username": "bad name!", "password": PASSWORD},
        {"username": "valid_name", "password": "short"},
    ],
)
def test_invalid_registration_returns_422(client, payload):
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_with_wrong_password_or_unknown_user(make_client):
    make_client("alice")
    visitor = make_client()

    wrong = visitor.post("/api/auth/login", json={"username": "alice", "password": "wrong-password"})
    unknown = visitor.post("/api/auth/login", json={"username": "nobody", "password": PASSWORD})
    ok = visitor.post("/api/auth/login", json={"username": "ALICE", "password": PASSWORD})

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"] == "帳號或密碼錯誤"
    assert ok.status_code == 200
    assert visitor.get("/api/auth/me").json()["username"] == "alice"


def test_repeated_failed_logins_are_throttled(make_client):
    make_client("alice")
    visitor = make_client()
    for _ in range(5):
        visitor.post("/api/auth/login", json={"username": "alice", "password": "wrong-password"})

    response = visitor.post("/api/auth/login", json={"username": "alice", "password": PASSWORD})

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"


def test_logout_revokes_the_session(make_client, db):
    alice = make_client("alice")
    token = alice.cookies.get("sv_session")

    assert alice.post("/api/auth/logout").status_code == 204
    assert db.query(UserSession).count() == 0
    assert alice.get("/api/auth/me").status_code == 401
    reused = make_client().get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert reused.status_code == 401  # 登出後 token 立即失效


def test_session_endpoint_reports_login_state_without_401(make_client):
    visitor = make_client()
    assert visitor.get("/api/auth/session").json() == {"authenticated": False, "user": None}

    alice = make_client("alice")
    body = alice.get("/api/auth/session").json()
    assert body["authenticated"] is True
    assert body["user"]["username"] == "alice"

    alice.post("/api/auth/logout")
    response = alice.get("/api/auth/session")
    assert response.status_code == 200
    assert response.json()["authenticated"] is False


def test_bearer_token_can_be_used_by_api_clients(make_client):
    token = make_client("alice").cookies.get("sv_session")

    response = make_client().get("/api/portfolio", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_expired_session_is_rejected(auth_client, set_now):
    set_now(DEFAULT_NOW + timedelta(days=get_settings().session_days, minutes=1))

    response = auth_client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.parametrize(("method", "path"), PROTECTED)
def test_personal_endpoints_require_login(client, method, path):
    response = getattr(client, method)(path)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_market_data_is_public(client):
    assert client.get("/api/market/status").status_code == 200
    assert client.get("/api/health").status_code == 200


def test_registration_can_be_disabled(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "registration_enabled", False)

    response = client.post("/api/auth/register", json={"username": "alice", "password": PASSWORD})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "REGISTRATION_DISABLED"
