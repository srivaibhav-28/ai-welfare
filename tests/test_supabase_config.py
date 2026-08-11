import importlib


def test_supabase_manager_uses_publishable_key_alias(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-publishable-key")

    import app.config as config_module
    config_module = importlib.reload(config_module)

    assert config_module.config.SUPABASE_URL == "https://example.supabase.co"
    assert config_module.config.SUPABASE_ANON_KEY == "test-publishable-key"
