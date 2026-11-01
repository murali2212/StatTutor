import pytest

from backend import db


def test_user_schemas_are_distinct_and_not_user_controlled():
    first = db.schema_for_user("b38cb52a-dc29-4581-9c89-bf43f75056a4")
    second = db.schema_for_user("017274da-1d3b-4151-871e-0a55537fec47")
    assert first.startswith("stattutor_")
    assert first != second
    with pytest.raises(ValueError):
        db.schema_for_user('"; DROP SCHEMA public;--')


def test_local_auth_configuration_is_disabled():
    from fastapi.testclient import TestClient
    from backend.main import app

    response = TestClient(app).get("/api/auth/config")
    assert response.status_code == 200
    assert response.json() == {
        "auth_enabled": False,
        "deployment_ready": True,
        "missing_settings": [],
        "supabase_url": None,
        "supabase_anon_key": None,
    }


def test_openai_compatible_provider_sends_user_key(monkeypatch):
    from backend import ai

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "OK"}}]}

    captured = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response()

    monkeypatch.setattr(ai.httpx, "post", fake_post)
    assert ai.call_provider("groq", "test-model", "my-private-key", []) == "OK"
    assert captured["headers"]["Authorization"] == "Bearer my-private-key"


def test_api_keys_are_encrypted_in_supabase_mode(monkeypatch):
    from cryptography.fernet import Fernet
    from backend import secret_store

    monkeypatch.setattr(db, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(db, "APP_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
    encrypted = secret_store.encrypt_api_key("provider-secret")
    assert encrypted.startswith("enc:v1:")
    assert encrypted != "provider-secret"
    assert secret_store.decrypt_api_key(encrypted) == "provider-secret"


def test_protected_api_requires_a_bearer_token(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app

    monkeypatch.setattr(db, "SUPABASE_ENABLED", True)
    response = TestClient(app).get("/api/status")
    assert response.status_code == 401


def test_access_token_is_forwarded_to_supabase(monkeypatch):
    from backend import auth

    class Response:
        status_code = 200
        is_error = False

        @staticmethod
        def json():
            return {"id": "b38cb52a-dc29-4581-9c89-bf43f75056a4"}

    captured = {}

    def fake_get(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response()

    monkeypatch.setattr(db, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(db, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(db, "SUPABASE_ANON_KEY", "public-key")
    monkeypatch.setattr(auth.httpx, "get", fake_get)
    user_id = auth.verify_access_token("signed-access-token")
    assert user_id == "b38cb52a-dc29-4581-9c89-bf43f75056a4"
    assert captured["headers"]["Authorization"] == "Bearer signed-access-token"


def test_unconfigured_vercel_returns_actionable_setup_response(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app

    monkeypatch.setattr(db, "IS_VERCEL", True)
    monkeypatch.setattr(db, "SUPABASE_ENABLED", False)
    response = TestClient(app).get("/api/auth/config")
    assert response.status_code == 200
    assert response.json()["deployment_ready"] is False
    assert "SUPABASE_DB_URL" in response.json()["missing_settings"]
    protected = TestClient(app).get("/api/status")
    assert protected.status_code == 503
    assert "redeploy" in protected.json()["detail"]
