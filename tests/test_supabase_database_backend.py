import importlib


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def test_database_uses_supabase_backend_when_configured(monkeypatch, tmp_path):
    class FakeRequests:
        def __init__(self):
            self.calls = []

        def get(self, url, headers=None, params=None, timeout=8):
            self.calls.append(("GET", url, params))
            return FakeResponse([{"id": "usr-1", "email": "demo@example.com"}])

    fake_requests = FakeRequests()

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "test-key")
    monkeypatch.setenv("DATA_STORE_FILE", str(tmp_path / "data_store.json"))

    import app.database as database_module
    import app.supabase_db as supabase_db_module

    database_module = importlib.reload(database_module)
    supabase_db_module = importlib.reload(supabase_db_module)
    monkeypatch.setattr(supabase_db_module, "requests", fake_requests)
    monkeypatch.setattr(supabase_db_module, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(supabase_db_module, "SUPABASE_KEY", "test-key")
    monkeypatch.setattr(database_module, "supabase_db", supabase_db_module.supabase_db)
    monkeypatch.setattr(database_module, "USE_SUPABASE", True)

    db = database_module.Database()
    users = db.get_users()

    assert users[0]["email"] == "demo@example.com"
    assert fake_requests.calls[0][0] == "GET"
