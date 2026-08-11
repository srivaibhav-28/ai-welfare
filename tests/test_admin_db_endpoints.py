from fastapi.testclient import TestClient

from run import app
from app.database.supabase_db import db as supabase_db


def test_admin_db_table_endpoints(monkeypatch):
    class FakeSupabaseDB:
        def __init__(self):
            self.rows = []
            self.data = {"users": [{"id": "usr-admin-01", "email": "admin@welfare.gov", "password_hash": "admin123", "role": "admin", "name": "Admin"}]}

        def save_data(self):
            pass

        def is_configured(self):
            return True

        def get_user_by_id(self, user_id):
            for u in self.data.get("users", []):
                if u.get("id") == user_id:
                    return u
            return {"id": user_id, "email": "admin@welfare.gov", "role": "admin", "name": "Admin"}

        def get_user_by_email(self, email):
            for u in self.data.get("users", []):
                if u.get("email") == email:
                    return u
            return {"id": "usr-admin-01", "email": email, "role": "admin", "name": "Admin"}

        def get_users(self):
            return self.data.get("users", [])

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
    fake_db.data["users"] = [{"id": "u1", "email": "demo@example.com"}]
    monkeypatch.setattr("app.database.supabase_db.db", fake_db)

    client = TestClient(app)

    token = "token_usr-admin-01_1"
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/admin/db/users", headers=headers)
    assert response.status_code == 200
    res_list = response.json()
    assert len(res_list) >= 1
    assert any(u.get("email") in ["demo@example.com", "admin@welfare.gov"] for u in res_list)

    create_response = client.post("/api/admin/db/schemes", json={"id": "s1", "name": "Demo"}, headers=headers)
    assert create_response.status_code == 200
    assert create_response.json()["name"] == "Demo"
