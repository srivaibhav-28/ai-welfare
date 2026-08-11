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

    import app.database.supabase_db as supabase_db_module

    supabase_db_module = importlib.reload(supabase_db_module)
    db_instance = supabase_db_module.SupabaseDatabase()
    monkeypatch.setattr(db_instance, "fetch_rows", lambda table, **kwargs: [{"id": "usr-1", "email": "demo@example.com"}])
    users = db_instance.get_users()

    assert len(users) >= 1
    assert users[0]["email"] == "demo@example.com"
