import os
import sys
import uuid
import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from api.applications import app
from app.database.supabase_db import db

client = TestClient(app)

def test_full_payment_flow():
    print("=== STARTING FULL PAYMENT FLOW VERIFICATION ===")
    
    # 1. Create a dummy user
    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    user_email = f"citizen_{uuid.uuid4().hex[:6]}@example.com"
    user_data = {
        "id": user_id,
        "email": user_email,
        "name": "Test Citizen",
        "mobile_number": "9876543210",
        "password_hash": "hashed_pass_123",
        "role": "citizen",
        "is_verified": True
    }
    db.add_user(user_data)
    print(f"[STEP 1] Created user: {user_id} ({user_email})")

    # 2. Create a dummy scheme
    scheme_id = f"scheme-{uuid.uuid4().hex[:6]}"
    scheme_data = {
        "id": scheme_id,
        "name": "PM Kisan Samman Nidhi",
        "category": "Agriculture",
        "description": "Financial benefit scheme for farmers",
        "benefits": "₹6,000 per year",
        "amount": 6000.00
    }
    db.add_scheme(scheme_data)
    print(f"[STEP 2] Created scheme: {scheme_id}")

    # 3. Create a dummy application
    app_id = f"app-{uuid.uuid4().hex[:6]}"
    app_data = {
        "id": app_id,
        "user_id": user_id,
        "user_name": "Test Citizen",
        "user_email": user_email,
        "scheme_id": scheme_id,
        "scheme_name": "PM Kisan Samman Nidhi",
        "status": "Under Verification",
        "applied_date": datetime.date.today().isoformat(),
        "uploaded_documents": [],
        "remarks": "Initial submission"
    }
    db.add_application(app_data)
    print(f"[STEP 3] Created application: {app_id}")

    # Create admin auth headers
    from app.services.auth_service import create_access_token
    admin_token = create_access_token({"sub": "usr-admin-aadc2d", "email": "admin@welfare.gov", "role": "admin", "id": "usr-admin-aadc2d"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    citizen_token = create_access_token({"sub": user_id, "email": user_email, "role": "citizen", "id": user_id})
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    # 4. Admin Approves Application
    approve_res = client.put(
        f"/api/applications/{app_id}/status",
        json={"status": "Approved", "remarks": "Approved by Welfare Officer"},
        headers=admin_headers
    )
    print(f"[STEP 4] Approval response status code: {approve_res.status_code}")
    assert approve_res.status_code == 200, f"Approval failed: {approve_res.text}"
    
    # 5. Check if Payment Record exists in DB
    db_payments = db.get_payments(application_id=app_id)
    print(f"[STEP 5] DB Payments for application {app_id}: {db_payments}")
    assert len(db_payments) == 1, f"Expected 1 payment record in DB, found {len(db_payments)}"
    pay_rec = db_payments[0]
    assert pay_rec["amount"] == 6000.00
    assert pay_rec["payment_status"] == "Pending"
    assert pay_rec["user_id"] == user_id

    # 6. Admin Approves Application AGAIN (Duplicate check)
    approve_res2 = client.put(
        f"/api/applications/{app_id}/status",
        json={"status": "Approved", "remarks": "Duplicate approval attempt"},
        headers=admin_headers
    )
    assert approve_res2.status_code == 200
    db_payments_after_dup = db.get_payments(application_id=app_id)
    print(f"[STEP 6] DB Payments after duplicate approval attempt: {len(db_payments_after_dup)}")
    assert len(db_payments_after_dup) == 1, "Duplicate payment record created!"

    # 7. Admin Payment API GET /api/payments
    admin_pay_res = client.get("/api/payments", headers=admin_headers)
    print(f"[STEP 7] GET /api/payments status code: {admin_pay_res.status_code}")
    assert admin_pay_res.status_code == 200
    admin_pay_data = admin_pay_res.json()
    assert admin_pay_data.get("status") == "success"
    assert isinstance(admin_pay_data.get("payments"), list)
    matching_admin_pay = [p for p in admin_pay_data["payments"] if p["application_id"] == app_id]
    assert len(matching_admin_pay) == 1, "Payment not found in GET /api/payments"

    # 8. Citizen Payment API GET /api/payments/me
    cit_pay_res = client.get("/api/payments/me", headers=citizen_headers)
    print(f"[STEP 8] GET /api/payments/me status code: {cit_pay_res.status_code}")
    assert cit_pay_res.status_code == 200, f"GET /api/payments/me failed: {cit_pay_res.status_code} - {cit_pay_res.text}"
    cit_pay_data = cit_pay_res.json()
    print(f"[STEP 8] GET /api/payments/me response payload: {cit_pay_data}")
    assert cit_pay_data.get("status") == "success"
    assert isinstance(cit_pay_data.get("payments"), list)
    matching_cit_pay = [p for p in cit_pay_data["payments"] if p["application_id"] == app_id]
    assert len(matching_cit_pay) == 1, "Payment not found in GET /api/payments/me"

    print("\n=== ALL BACKEND CHECKS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_full_payment_flow()
