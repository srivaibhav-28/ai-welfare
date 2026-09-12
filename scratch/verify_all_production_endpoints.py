import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from api.applications import app as app_applications
from api.admin import app as app_admin
from api.eligibility import app as app_eligibility
from app.services.auth_service import create_access_token

def test_production_endpoints():
    print("=== VERIFYING ALL 5 PRODUCTION ENDPOINTS ===")

    admin_token = create_access_token({
        "sub": "usr-admin-aadc2d",
        "email": "admin@welfare.gov",
        "role": "admin",
        "id": "usr-admin-aadc2d"
    })
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. GET /api/payments
    client_app = TestClient(app_applications)
    res_payments = client_app.get("/api/payments", headers=admin_headers)
    print(f"1. GET /api/payments status code: {res_payments.status_code}")
    assert res_payments.status_code == 200, f"Failed: {res_payments.text}"
    print(f"   Payload count: {res_payments.json().get('count')}")

    # 2. GET /api/payments/analytics
    res_pay_analytics = client_app.get("/api/payments/analytics", headers=admin_headers)
    print(f"2. GET /api/payments/analytics status code: {res_pay_analytics.status_code}")
    assert res_pay_analytics.status_code == 200, f"Failed: {res_pay_analytics.text}"
    assert "analytics" in res_pay_analytics.json()

    # 3. GET /api/admin/analytics
    client_admin = TestClient(app_admin)
    res_admin_analytics = client_admin.get("/api/admin/analytics", headers=admin_headers)
    print(f"3. GET /api/admin/analytics status code: {res_admin_analytics.status_code}")
    assert res_admin_analytics.status_code == 200, f"Failed: {res_admin_analytics.text}"
    assert "total_users" in res_admin_analytics.json()

    # 4. GET /api/admin/db/users
    res_db_users = client_admin.get("/api/admin/db/users", headers=admin_headers)
    print(f"4. GET /api/admin/db/users status code: {res_db_users.status_code}")
    assert res_db_users.status_code == 200, f"Failed: {res_db_users.text}"
    assert isinstance(res_db_users.json(), list)

    # 5. POST /api/evaluate
    client_eligibility = TestClient(app_eligibility)
    eval_payload = {
        "name": "Verification User",
        "email": "verify@example.com",
        "age": 35,
        "gender": "Male",
        "annual_income": 120000,
        "occupation": "Farmer",
        "caste_category": "OBC",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "is_disabled": False,
        "is_student": False,
        "farmer_status": True
    }
    res_eval = client_eligibility.post("/api/evaluate", json=eval_payload)
    print(f"5. POST /api/evaluate status code: {res_eval.status_code}")
    assert res_eval.status_code == 200, f"Failed: {res_eval.text}"
    eval_data = res_eval.json()
    print(f"   Evaluated schemes: {eval_data.get('total_evaluated', len(eval_data.get('recommendations', [])))}")

    print("\n=== ALL 5 ENDPOINTS PASSED WITH HTTP 200 SUCCESS ===")

if __name__ == "__main__":
    test_production_endpoints()
