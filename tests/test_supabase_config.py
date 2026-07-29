import importlib


def test_supabase_manager_uses_publishable_key_alias(monkeypatch):
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "test-publishable-key")

    import app.supabase_client as supabase_module
    supabase_module = importlib.reload(supabase_module)

    manager = supabase_module.SupabaseManager()

    assert manager.url == "https://example.supabase.co"
    assert manager.key == "test-publishable-key"
