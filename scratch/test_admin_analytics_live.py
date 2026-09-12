import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from run import app

client = TestClient(app)

def test_analytics():
    print("=" * 80)
    print("        TESTING /api/admin/analytics LIVE SUPABASE RESPONSE          ")
    print("=" * 80)

    # 1. Admin login to get JWT token
    login_res = client.post("/api/admin/login", json={
        "email": "admin@welfare.gov",
        "password": "Admin@123456"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. GET /api/admin/analytics
    res = client.get("/api/admin/analytics", headers=headers)
    assert res.status_code == 200, f"Analytics failed ({res.status_code}): {res.text}"
    data = res.json()

    print("\nANALYTICS DATA RETURNED FROM LIVE SUPABASE:")
    print(f"  - total_users         : {data.get('total_users')}")
    print(f"  - total_schemes       : {data.get('total_schemes')}")
    print(f"  - total_applications  : {data.get('total_applications')}")
    print(f"  - pending_applications: {data.get('pending_applications')}")
    print(f"  - approved_applications: {data.get('approved_applications')}")
    print(f"  - rejected_applications: {data.get('rejected_applications')}")

    assert data.get("total_users", 0) > 0, "total_users should be > 0!"
    assert data.get("total_schemes", 0) > 0, "total_schemes should be > 0!"
    assert data.get("total_applications", 0) > 0, "total_applications should be > 0!"

    print("\n" + "=" * 80)
    print("        LIVE SUPABASE ANALYTICS VERIFIED 100% SUCCESSFUL!            ")
    print("=" * 80)

if __name__ == "__main__":
    test_analytics()
