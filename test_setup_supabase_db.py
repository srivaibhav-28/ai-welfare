from setup_supabase_db import build_database_url


def test_build_database_url_encodes_password_with_at_symbol():
    raw_url = "postgresql://postgres:SriVaibhav@2007@db.example.com:5432/postgres"
    expected = "postgresql://postgres:SriVaibhav%402007@db.example.com:5432/postgres"

    assert build_database_url(raw_url) == expected
