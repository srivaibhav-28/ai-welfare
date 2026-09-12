import os
import sys
import traceback

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from run import app

client = TestClient(app)

def test_all_admin_endpoints():
    print("=" * 80)
    print("        TESTING ALL ADMIN ENDPOINTS FOR ANY 500 INTERNAL SERVER ERRORS ")
    print("=" * 80)

    # 1. POST /api/admin/login
    print("\n1. POST /api/admin/login...")
    res_login = client.post("/api/admin/login", json={
        "email": "admin@welfare.gov",
        "password": "Admin@123456"
    })
    print(f"   Status Code: {res_login.status_code}")
    print(f"   Body: {res_login.text}")
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. GET /api/admin/analytics
    print("\n2. GET /api/admin/analytics...")
    res_analytics = client.get("/api/admin/analytics", headers=headers)
    print(f"   Status Code: {res_analytics.status_code}")
    assert res_analytics.status_code == 200, f"Analytics failed: {res_analytics.text}"

    # 3. GET /api/admin/users
    print("\n3. GET /api/admin/users...")
    res_users = client.get("/api/admin/users", headers=headers)
    print(f"   Status Code: {res_users.status_code}")
    assert res_users.status_code == 200, f"Get users failed: {res_users.text}"

    # 4. GET /api/admin/db/users
    print("\n4. GET /api/admin/db/users...")
    res_db_users = client.get("/api/admin/db/users", headers=headers)
    print(f"   Status Code: {res_db_users.status_code}")
    assert res_db_users.status_code == 200, f"Get db users failed: {res_db_users.text}"

    # 5. GET /api/admin/db/schemes
    print("\n5. GET /api/admin/db/schemes...")
    res_db_schemes = client.get("/api/admin/db/schemes", headers=headers)
    print(f"   Status Code: {res_db_schemes.status_code}")
    assert res_db_schemes.status_code == 200, f"Get db schemes failed: {res_db_schemes.text}"

    # 6. GET /api/admin/db/applications
    print("\n6. GET /api/admin/db/applications...")
    res_db_apps = client.get("/api/admin/db/applications", headers=headers)
    print(f"   Status Code: {res_db_apps.status_code}")
    assert res_db_apps.status_code == 200, f"Get db applications failed: {res_db_apps.text}"

    # 7. GET /api/admin/notifications
    print("\n7. GET /api/admin/notifications...")
    res_notif = client.get("/api/admin/notifications", headers=headers)
    print(f"   Status Code: {res_notif.status_code}")
    assert res_notif.status_code == 200, f"Get notifications failed: {res_notif.text}"

    # 8. GET /api/admin/supabase-status
    print("\n8. GET /api/admin/supabase-status...")
    res_supa = client.get("/api/admin/supabase-status", headers=headers)
    print(f"   Status Code: {res_supa.status_code}")
    assert res_supa.status_code == 200, f"Get supabase status failed: {res_supa.text}"

    print("\n" + "=" * 80)
    print("        ALL ADMIN ENDPOINTS EXECUTED WITH ZERO 500 ERRORS!             ")
    print("=" * 80)

if __name__ == "__main__":
    test_all_admin_endpoints()
