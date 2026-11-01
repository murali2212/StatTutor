import os, tempfile
os.environ["STATTUTOR_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
from fastapi.testclient import TestClient
from backend.main import app
from backend import ai

c = TestClient(app)

def test_math_endpoint():
    r = c.post("/api/math/descriptive", json={"data": [2, 4, 4, 4, 5, 5, 7, 9], "sample": False})
    assert r.status_code == 200 and r.json()["sd"] == 2
    assert c.post("/api/math/descriptive", json={"data": [], "sample": True}).status_code == 400

def test_chat_without_key_asks_for_key():
    r = c.post("/api/tutor/chat", json={"message": "hi"})
    assert r.status_code == 409 and r.json()["code"] == "no_key"

def test_bad_key_is_not_saved(monkeypatch):
    def boom(*a, **k): raise ai.ProviderError("invalid", "bad")
    monkeypatch.setattr(ai, "call_provider", boom)
    r = c.post("/api/keys", json={"provider": "groq", "api_key": "x" * 20})
    assert r.status_code == 400 and c.get("/api/keys").json() == []

def _seed(*keys):
    from backend import db
    with db.conn() as con:
        con.execute("DELETE FROM api_keys"); con.execute("DELETE FROM messages"); con.execute("DELETE FROM learner")
        for k in keys:
            con.execute("INSERT INTO api_keys(provider, model, api_key) VALUES ('gemini','m',?)", (k,))

def _fake(provider, model, key, messages, timeout=60):
    if key.startswith("DEAD"): raise ai.ProviderError("quota", "limit")
    return "Lesson text"

def test_failover_to_next_key(monkeypatch):
    monkeypatch.setattr(ai, "call_provider", _fake)
    _seed("DEAD-key-000001", "LIVE-key-000002")
    r = c.post("/api/tutor/chat", json={"message": "teach mean"})
    assert r.status_code == 200 and r.json()["reply"] == "Lesson text"
    st = {k["status"] for k in c.get("/api/keys").json()}
    assert st == {"exhausted", "active"}

def test_all_exhausted_then_new_key_resumes(monkeypatch):
    monkeypatch.setattr(ai, "call_provider", _fake)
    _seed("DEAD-key-000001")
    r = c.post("/api/tutor/chat", json={"message": "teach median"})
    assert r.status_code == 429 and r.json()["code"] == "api_exhausted"
    assert c.get("/api/tutor/history").json() == []          # nothing half-saved
    assert c.post("/api/keys", json={"provider": "gemini", "api_key": "LIVE-key-000009"}).status_code == 200
    r = c.post("/api/tutor/chat", json={"message": "teach median"})   # same message retried
    assert r.status_code == 200
    assert [m["role"] for m in c.get("/api/tutor/history").json()] == ["user", "assistant"]

def test_keys_are_masked():
    _seed("SECRET-KEY-VALUE-123456")
    assert "SECRET-KEY-VALUE" not in str(c.get("/api/keys").json())
