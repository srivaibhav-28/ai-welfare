import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import uuid
import datetime
from fastapi.testclient import TestClient

from run import app
from app.database.supabase_db import db

client = TestClient(app)

def run_verification():
    print("=== STARTING PAYMENT MANAGEMENT MODULE VERIFICATION ===")

    # 1. Ensure test admin user exists and obtain admin headers
    from app.admin_constants import ADMIN_USER_ID, ADMIN_EMAIL, ADMIN_NAME
    from app.services.auth_service import create_access_token
    admin_token = create_access_token({
        "sub": ADMIN_USER_ID,
        "email": ADMIN_EMAIL,
        "role": "admin",
        "name": ADMIN_NAME
    })
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create test citizen user with bank details in profile
    user_id = f"usr-test-{uuid.uuid4().hex[:6]}"
    test_user = {
        "id": user_id,
        "email": f"testbank_{uuid.uuid4().hex[:4]}@example.com",
        "password_hash": "$2b$12$eImiTXuWVxfM37uY4JANjO5E.y5b3N6LhH5.aW7a.H6q.",
        "name": "Ramesh Kumar",
        "role": "citizen",
        "profile": {
            "full_name": "Ramesh Kumar",
            "bank_account_number": "987654321098",
            "ifsc_code": "SBIN0001234",
            "bank_account_available": True
        }
    }
    db.add_user(test_user)
    print(f"[PASS] Test citizen created with bank details (Acc: 987654321098, IFSC: SBIN0001234)")

    # 3. Create test payment record
    pay_id = f"pay-test-{uuid.uuid4().hex[:6]}"
    app_id = f"app-test-{uuid.uuid4().hex[:6]}"
    payment_rec = {
        "id": pay_id,
        "payment_id": pay_id,
        "application_id": app_id,
        "user_id": user_id,
        "scheme_id": "scheme-pmkisan",
        "scheme_name": "PM-KISAN Samman Nidhi",
        "beneficiary_name": "Ramesh Kumar",
        "amount": 6000.0,
        "payment_status": "Pending",
        "payment_reference": "",
        "approved_by": "admin@welfare.gov",
        "approved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "paid_at": None,
        "remarks": "Test initial payment",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    db.add_payment(payment_rec)
    print(f"[PASS] Test payment record created (ID: {pay_id}, Status: Pending)")

    # 4. Test GET /api/payments (Check payment enrichment & analytics)
    res_get = client.get("/api/payments", headers=admin_headers)
    assert res_get.status_code == 200, f"GET /api/payments failed: {res_get.text}"
    data_get = res_get.json()
    assert data_get.get("status") == "success"
    payments_list = data_get.get("payments", [])
    found = [p for p in payments_list if p.get("id") == pay_id or p.get("payment_id") == pay_id]
    assert len(found) > 0, f"Payment {pay_id} not found in GET /api/payments response"
    p_obj = found[0]
    assert p_obj.get("bank_account_number") == "987654321098"
    assert p_obj.get("ifsc_code") == "SBIN0001234"
    assert p_obj.get("account_holder_name") == "Ramesh Kumar"
    assert "analytics" in data_get
    print("[PASS] GET /api/payments verified: returned enriched payment with beneficiary bank details and analytics cards")

    # 5. Test PUT /api/payments/{payment_id}/status -> Processing
    res_proc = client.put(f"/api/payments/{pay_id}/status", json={
        "payment_status": "Processing",
        "payment_reference": "",
        "remarks": "Sent to bank clearance"
    }, headers=admin_headers)
    assert res_proc.status_code == 200, f"PUT status to Processing failed: {res_proc.text}"
    p_proc = db.get_payment_by_id(pay_id)
    assert p_proc.get("payment_status") == "Processing"
    print("[PASS] Updated payment status to Processing successfully")

    # 6. Test PUT /api/payments/{payment_id}/status -> Completed (Simulated DBT Payment)
    res_comp = client.put(f"/api/payments/{pay_id}/status", json={
        "payment_status": "Completed",
        "payment_reference": "", # Empty reference to trigger auto fake UTR generation
        "remarks": "DBT transfer cleared"
    }, headers=admin_headers)
    assert res_comp.status_code == 200, f"PUT status to Completed failed: {res_comp.text}"
    p_comp = db.get_payment_by_id(pay_id)
    assert p_comp.get("payment_status") == "Completed"
    assert p_comp.get("payment_reference", "").startswith("UTR"), f"Expected generated fake UTR, got: {p_comp.get('payment_reference')}"
    assert p_comp.get("paid_at") is not None, "Expected paid_at timestamp to be set"
    print(f"[PASS] Updated payment status to Completed: Auto-generated UTR = {p_comp.get('payment_reference')}, Paid Date = {p_comp.get('paid_at')[:10]}")

    # 7. Test Analytics after Completed
    res_get2 = client.get("/api/payments", headers=admin_headers)
    analytics2 = res_get2.json().get("analytics", {})
    assert analytics2.get("completed", 0) >= 1
    assert analytics2.get("total_amount_paid", 0) >= 6000.0
    print(f"[PASS] Analytics updated automatically: Completed = {analytics2.get('completed')}, Total Paid = INR {analytics2.get('total_amount_paid')}")

    print("=== ALL VERIFICATION TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_verification()
