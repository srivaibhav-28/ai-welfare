import sys
import os
import uuid
import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.services.email_service import EmailNotificationService

# Patch send_email to run verification suite instantly without SMTP network delays
patch.object(EmailNotificationService, 'send_email', return_value=(True, "Mocked")).start()

from run import app
from app.database.supabase_db import db
from app.services.auth_service import create_access_token

client = TestClient(app)

def run_verifications():
    print("==========================================================================")
    print("  VERIFICATION SUITE: APPLICATION STATUS UPDATE & PAYMENT CREATION")
    print("==========================================================================")

    # 1. Admin Token Setup
    admin_user = db.ensure_single_admin()
    admin_token = create_access_token({
        "sub": admin_user["id"],
        "email": admin_user["email"],
        "role": "admin",
        "name": admin_user.get("name", "Admin")
    })
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] Admin Token Generated & Auth Ready")

    # 2. Register & Verify a Citizen User
    test_email = f"test_citizen_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = client.post("/api/auth/register", json={
        "name": "Test Citizen",
        "email": test_email,
        "mobile_number": "9876543210",
        "password": "Password123",
        "role": "citizen"
    })
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    
    verify_res = client.post("/api/auth/verify-otp", json={"email": test_email, "otp": "123456"})
    assert verify_res.status_code == 200, f"OTP verification failed: {verify_res.text}"
    citizen_token = verify_res.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    print(f"[PASS] Citizen Registered & Verified ({test_email})")

    # 3. Create Scheme Application (Status = Applied)
    scheme_id = "scheme-001"
    app_res = client.post("/api/applications/direct-apply", json={
        "scheme_id": scheme_id,
        "uploaded_documents": {"Aadhaar Card": "aadhaar.jpg"}
    }, headers=citizen_headers)
    assert app_res.status_code == 200, f"Application creation failed: {app_res.text}"
    app_data = app_res.json()["application"]
    app_id = app_data["id"]
    print(f"[PASS] Application Created: ID={app_id}, Initial Status={app_data['status']}")
    assert app_data["status"] in ["Applied", "Under Fraud Review"]

    # 4. Test Transition: Applied -> Under Verification
    status_res1 = client.put(f"/api/applications/{app_id}/status", json={
        "status": "Under Verification",
        "remarks": "Documents being verified by officer"
    }, headers=admin_headers)
    assert status_res1.status_code == 200, f"Status update to Under Verification failed: {status_res1.text}"
    updated_app1 = status_res1.json()["application"]
    assert updated_app1["status"] == "Under Verification"
    print(f"[PASS] Status Transition: Applied -> Under Verification (HTTP {status_res1.status_code})")

    # 5. Test Transition: Under Verification -> Approved
    status_res2 = client.put(f"/api/applications/{app_id}/status", json={
        "status": "Approved",
        "remarks": "Approved by welfare officer"
    }, headers=admin_headers)
    assert status_res2.status_code == 200, f"Status update to Approved failed: {status_res2.text}"
    updated_app2 = status_res2.json()["application"]
    assert updated_app2["status"] == "Approved"
    print(f"[PASS] Status Transition: Under Verification -> Approved (HTTP {status_res2.status_code})")

    # 6. Verify Payment Record Created Automatically (Exactly 1 Payment)
    payments = db.get_payments(application_id=app_id)
    assert len(payments) == 1, f"Expected 1 payment record, found {len(payments)}"
    pay_record = payments[0]
    assert pay_record["application_id"] == app_id
    assert pay_record["payment_status"] == "Pending"
    assert pay_record["amount"] == 6000.00
    print(f"[PASS] Payment Record Created: ID={pay_record['id']}, Status={pay_record['payment_status']}, Amount=INR {pay_record['amount']}")

    # 7. Test Duplicate Status Update to Approved (No Duplicate Payment Created)
    status_res_dup = client.put(f"/api/applications/{app_id}/status", json={
        "status": "Approved",
        "remarks": "Re-approving test"
    }, headers=admin_headers)
    assert status_res_dup.status_code == 200
    payments_dup = db.get_payments(application_id=app_id)
    assert len(payments_dup) == 1, f"Duplicate payment created! Count = {len(payments_dup)}"
    print("[PASS] Idempotency Check Passed: Re-approving app creates NO duplicate payments")

    # 8. Test Transition: Under Verification -> Rejected (on a new application)
    app_res2 = client.post("/api/applications/direct-apply", json={
        "scheme_id": "scheme-002",
        "uploaded_documents": {"Aadhaar Card": "aadhaar.jpg"}
    }, headers=citizen_headers)
    assert app_res2.status_code == 200
    app_id2 = app_res2.json()["application"]["id"]

    client.put(f"/api/applications/{app_id2}/status", json={
        "status": "Under Verification",
        "remarks": "Checking eligibility"
    }, headers=admin_headers)

    status_res3 = client.put(f"/api/applications/{app_id2}/status", json={
        "status": "Rejected",
        "remarks": "Income exceeds eligibility threshold"
    }, headers=admin_headers)
    assert status_res3.status_code == 200, f"Status update to Rejected failed: {status_res3.text}"
    updated_app3 = status_res3.json()["application"]
    assert updated_app3["status"] == "Rejected"
    print(f"[PASS] Status Transition: Under Verification -> Rejected (HTTP {status_res3.status_code})")

    # 9. Verify Citizen Dashboard Applications Endpoint
    citizen_apps_res = client.get("/api/applications", headers=citizen_headers)
    assert citizen_apps_res.status_code == 200
    c_apps = citizen_apps_res.json()
    c_app_ids = [a["id"] for a in c_apps]
    assert app_id in c_app_ids and app_id2 in c_app_ids
    print(f"[PASS] Citizen Dashboard API Verified: Fetched {len(c_apps)} applications for citizen")

    # 10. Verify Admin Dashboard Applications Endpoint
    admin_apps_res = client.get("/api/admin/applications", headers=admin_headers)
    assert admin_apps_res.status_code == 200
    a_apps = admin_apps_res.json()
    print(f"[PASS] Admin Dashboard API Verified: Total applications across system = {len(a_apps)}")

    # 11. Verify Payment List API
    admin_payments_res = client.get("/api/payments", headers=admin_headers)
    assert admin_payments_res.status_code == 200
    payments_payload = admin_payments_res.json()
    assert "payments" in payments_payload and "analytics" in payments_payload
    print(f"[PASS] Admin Payment Management API Verified: Total payments = {payments_payload['count']}")

    print("\n==========================================================================")
    print("  [SUCCESS] ALL VERIFICATIONS PASSED PERFECTLY WITH ZERO ERRORS!")
    print("==========================================================================")

if __name__ == "__main__":
    run_verifications()
