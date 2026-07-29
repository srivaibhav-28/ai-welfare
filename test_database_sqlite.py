import os
import sqlite3

from app.database import Database


def test_database_creates_sqlite_tables_and_persists_users(tmp_path):
    db_path = tmp_path / "data_store.json"
    db = Database(str(db_path))

    db.add_user({
        "id": "user-sqlite-1",
        "email": "persist@example.com",
        "password_hash": "hash",
        "name": "Persisted User",
        "mobile_number": "9999999999",
        "role": "citizen",
        "profile": {}
    })

    assert db.get_user_by_email("persist@example.com") is not None
    assert hasattr(db, "sqlite_file")
    assert os.path.exists(db.sqlite_file)

    conn = sqlite3.connect(db.sqlite_file)
    try:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    finally:
        conn.close()

    assert "users" in tables
    assert "schemes" in tables
    assert "applications" in tables

    reloaded = Database(str(db_path))
    assert reloaded.get_user_by_email("persist@example.com") is not None
