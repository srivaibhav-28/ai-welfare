from pathlib import Path


def test_supabase_schema_file_contains_required_tables():
    schema_path = Path(__file__).resolve().parents[1] / "supabase_schema.sql"
    assert schema_path.exists(), "Expected Supabase schema SQL file to exist"

    schema_sql = schema_path.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS users" in schema_sql
    assert "CREATE TABLE IF NOT EXISTS schemes" in schema_sql
    assert "CREATE TABLE IF NOT EXISTS applications" in schema_sql
    assert "CREATE TABLE IF NOT EXISTS user_documents" in schema_sql
