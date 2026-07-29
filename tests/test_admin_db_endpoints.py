from fastapi.testclient import TestClient

from app.main import app


def test_admin_db_table_endpoints(monkeypatch):
    class FakeSupabaseDB:
        def __init__(self):
            self.rows = []

        def is_configured(self):
            return True

        def fetch_rows(self, table, filters=None, select='*'):
            return [{"id": "u1", "email": "demo@example.com"}] if table == "users" else []

        def insert_row(self, table, data):
            self.rows.append((table, data))
            return data

        def update_row(self, table, filters, data):
            return {**data, **filters}

        def delete_rows(self, table, filters):
            return True

    fake_db = FakeSupabaseDB()
    monkeypatch.setattr("app.main.supabase_db", fake_db)

    client = TestClient(app)

    # Admin auth uses the same db object, so we provide a valid admin user via token logic
    from app.database import db as database_db
    admin_user = {"id": "usr-admin-01", "email": "admin@welfare.gov", "password_hash": "admin123", "role": "admin", "name": "Admin"}
    database_db.data["users"] = [admin_user]
    database_db.save_data()

    token = "token_usr-admin-01_1"
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/admin/db/users", headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["email"] == "demo@example.com"

    create_response = client.post("/api/admin/db/schemes", json={"id": "s1", "name": "Demo"}, headers=headers)
    assert create_response.status_code == 200
    assert create_response.json()["name"] == "Demo"
