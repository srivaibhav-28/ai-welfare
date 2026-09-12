import os
import sys
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock real email dispatches during test execution
from app.services.email_service import EmailNotificationService
patch.object(EmailNotificationService, 'send_email', return_value=(True, "Mocked")).start()

# Enable production environment simulation
os.environ["ENVIRONMENT"] = "production"

from run import app
from app.database.supabase_db import db
from app.services.auth_service import create_access_token

client = TestClient(app)

def run_suite():
    print("==========================================================================")
    print("  VERIFICATION SUITE: PAYMENT ROUTING, NOTIFICATIONS & SYSTEM INTEGRITY")
    print("==========================================================================")

    # 1. Generate Admin Token
    admin_user = db.ensure_single_admin()
    admin_token = create_access_token({
        "sub": admin_user["id"],
        "email": admin_user["email"],
        "role": "admin",
        "name": admin_user.get("name", "Admin")
    })
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] 1. Admin Token Created")

    # 2. Test GET /api/admin/notifications (Task 7 & Task 9 Requirement)
    notif_res = client.get("/api/admin/notifications", headers=admin_headers)
    assert notif_res.status_code == 200, f"/api/admin/notifications failed with {notif_res.status_code}: {notif_res.text}"
    notif_data = notif_res.json()
    assert isinstance(notif_data, list), "Expected list output from /api/admin/notifications"
    print(f"[PASS] 2. GET /api/admin/notifications returned HTTP 200 JSON ({len(notif_data)} notifications)")

    # 3. Test GET /api/payments (Task 9 Requirement)
    payments_res = client.get("/api/payments", headers=admin_headers)
    assert payments_res.status_code == 200, f"GET /api/payments failed with {payments_res.status_code}: {payments_res.text}"
    pay_data = payments_res.json()
    assert isinstance(pay_data, dict) and "payments" in pay_data and "analytics" in pay_data, "Invalid JSON structure from /api/payments"
    print(f"[PASS] 3. GET /api/payments returned HTTP 200 JSON (Count: {pay_data['count']})")

    # 4. Register Citizen & Test GET /api/payments/me (Task 9 Requirement)
    test_email = f"citizen_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/auth/register", json={
        "name": "Payment Citizen",
        "email": test_email,
        "mobile_number": "9876543210",
        "password": "Password123",
        "role": "citizen"
    })
    v_res = client.post("/api/auth/verify-otp", json={"email": test_email, "otp": "123456"})
    citizen_token = v_res.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    my_payments_res = client.get("/api/payments/me", headers=citizen_headers)
    assert my_payments_res.status_code == 200, f"GET /api/payments/me failed: {my_payments_res.text}"
    my_pay_data = my_payments_res.json()
    assert isinstance(my_pay_data, dict) and "payments" in my_pay_data, "Invalid JSON structure from /api/payments/me"
    print(f"[PASS] 4. GET /api/payments/me returned HTTP 200 JSON (Count: {my_pay_data['count']})")

    # 5. Create Application & Approve to Verify Payment Generation (Task 9 Requirement)
    app_res = client.post("/api/applications/direct-apply", json={
        "scheme_id": "scheme-001",
        "uploaded_documents": {"Aadhaar Card": "aadhaar.jpg"}
    }, headers=citizen_headers)
    assert app_res.status_code == 200
    app_id = app_res.json()["application"]["id"]

    approve_res = client.put(f"/api/applications/{app_id}/status", json={
        "status": "Approved",
        "remarks": "Approved during payment route test"
    }, headers=admin_headers)
    assert approve_res.status_code == 200, f"App approval failed: {approve_res.text}"
    assert approve_res.json()["application"]["status"] == "Approved"
    print(f"[PASS] 5. Application {app_id} Approved Successfully")

    # 6. Verify Exactly 1 Payment Generated
    created_payments = db.get_payments(application_id=app_id)
    assert len(created_payments) == 1, f"Expected 1 payment record, found {len(created_payments)}"
    pay_rec = created_payments[0]
    assert pay_rec["application_id"] == app_id
    assert pay_rec["payment_status"] == "Pending"
    print(f"[PASS] 6. Payment Record Created for Approved App: ID={pay_rec['id']}, Status={pay_rec['payment_status']}")

    # 7. Test PUT /api/payments/{id}/status Endpoint
    update_pay_res = client.put(f"/api/payments/{pay_rec['id']}/status", json={
        "payment_status": "Processing",
        "payment_reference": "TXN-987654",
        "remarks": "Processing DBT bank transfer"
    }, headers=admin_headers)
    assert update_pay_res.status_code == 200, f"Update payment status failed: {update_pay_res.text}"
    updated_p = update_pay_res.json()["payment"]
    assert updated_p["payment_status"] == "Processing"
    print(f"[PASS] 7. PUT /api/payments/{{id}}/status Updated Payment to Processing (Ref: TXN-987654)")

    # 8. Test Admin Applications List Still Works
    admin_apps_res = client.get("/api/admin/applications", headers=admin_headers)
    assert admin_apps_res.status_code == 200
    print(f"[PASS] 8. Admin Applications API Verified ({len(admin_apps_res.json())} total apps)")

    print("\n==========================================================================")
    print("  [SUCCESS] ALL VERIFICATION TASKS COMPLETED PERFECTLY WITH 0 ERRORS!")
    print("==========================================================================")

if __name__ == "__main__":
    run_suite()
