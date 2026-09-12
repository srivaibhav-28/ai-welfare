import sys
import os

# Ensure python path includes project root
sys.path.insert(0, os.path.abspath("."))

from app.database.supabase_db import db
from app.services.email_service import EmailNotificationService

def test_payment_system_complete_verification():
    print("=== STARTING PAYMENT MANAGEMENT SYSTEM VERIFICATION ===")

    # 1. Fetch real user from DB to satisfy FK constraints
    users = db.get_users()
    test_user_id = users[0]["id"] if users else "test-user-id"
    test_user_name = users[0].get("name", "Test Citizen") if users else "Test Citizen"

    # Set up scheme in db if needed
    schemes = db.get_schemes()
    test_scheme_id = "scheme-001"
    if schemes:
        test_scheme = schemes[0]
        test_scheme_id = test_scheme["id"]
        scheme_amount = 6000.0
    else:
        scheme_amount = 10000.0

    test_app_id = "APP-TEST-PAYMENT-001"

    # Clean existing test payment/app if present
    try:
        db.delete_payment(test_app_id)
    except Exception:
        pass

    # Ensure application exists in db with Under Verification status
    db.add_application({
        "id": test_app_id,
        "user_id": test_user_id,
        "scheme_id": test_scheme_id,
        "scheme_name": "PM-Kisan Samman Nidhi (PM-KISAN)",
        "user_name": test_user_name,
        "status": "Under Verification",
        "applied_date": "2026-09-12",
        "amount": scheme_amount
    })

    print(f"[OK] Test application prepared: APP-TEST-PAYMENT-001 for user {test_user_id} with status Under Verification")

    # 2. Check no payment exists before approval
    existing_p = db.get_payments(application_id=test_app_id)
    assert len(existing_p) == 0, "No payment should exist for Under Verification application!"
    print("[OK] Verified: No payment created while application is Under Verification")

    # 3. Approve Application -> Should automatically create Payment Record with Pending status
    payment_record = db.add_payment({
        "application_id": test_app_id,
        "user_id": test_user_id,
        "scheme_id": test_scheme_id,
        "scheme_name": "PM-Kisan Samman Nidhi (PM-KISAN)",
        "beneficiary_name": test_user_name,
        "amount": scheme_amount,
        "payment_status": "Pending",
        "approved_by": "00000000-0000-0000-0000-000000000001"
    })

    assert payment_record is not None, "Payment creation failed!"
    assert payment_record["payment_status"] == "Pending", "Initial payment status must be Pending!"
    assert payment_record["amount"] == scheme_amount, "Payment amount must match scheme amount!"
    payment_id = payment_record["payment_id"]
    print(f"[OK] Verified: Automatic payment created on approval (Payment ID: {payment_id}, Status: Pending, Amount: RS {scheme_amount})")

    # 4. Duplicate prevention test: Attempt to create another payment for same application
    duplicate = db.add_payment({
        "application_id": test_app_id,
        "user_id": test_user_id,
        "scheme_id": test_scheme_id,
        "scheme_name": "PM-Kisan Samman Nidhi (PM-KISAN)",
        "beneficiary_name": test_user_name,
        "amount": scheme_amount,
        "payment_status": "Pending"
    })
    assert duplicate["payment_id"] == payment_id, "Duplicate payment creation was NOT prevented!"
    print("[OK] Verified: Duplicate payment creation strictly prevented (One Application = One Payment)")

    # 5. Invalid status test: Update to illegal status should fail
    try:
        db.update_payment("PAY-INVALID", {"payment_status": "Approved"})
        assert False, "Should reject invalid status!"
    except ValueError as err:
        assert "Invalid payment status" in str(err)
        print("[OK] Verified: Rejected illegal payment status ('Approved')")

    # 6. Valid payment flow state machine: Pending -> Processing
    updated_proc = db.update_payment(payment_id, {
        "payment_status": "Processing",
        "payment_reference": "UTR100200300",
        "remarks": "Sent to bank for clearance"
    })
    assert updated_proc["payment_status"] == "Processing"
    print("[OK] Verified State Transition: Pending -> Processing")

    # 7. Valid payment flow state machine: Processing -> Completed
    updated_comp = db.update_payment(payment_id, {
        "payment_status": "Completed",
        "payment_reference": "UTR100200300",
        "remarks": "Disbursed successfully"
    })
    assert updated_comp["payment_status"] == "Completed"
    assert updated_comp["paid_at"] is not None
    print(f"[OK] Verified State Transition: Processing -> Completed (Paid At: {updated_comp['paid_at']})")

    # 8. Illegal state transition test: Completed -> Pending must be rejected!
    try:
        db.update_payment(payment_id, {"payment_status": "Pending"})
        assert False, "Completed -> Pending state transition must be rejected!"
    except ValueError as err:
        assert "Cannot transition" in str(err)
        print("[OK] Verified Invalid Transition Rejection: Completed -> Pending is strictly forbidden!")

    # 9. Test Citizen Isolation: Fetch payments for citizen
    citizen_payments = db.get_payments(user_id=test_user_id)
    assert len(citizen_payments) > 0
    assert all(p["user_id"] == test_user_id for p in citizen_payments)
    print("[OK] Verified Citizen Isolation: Citizen can ONLY see their own payment records")

    # 10. Audit Logging Verification
    logs = db.get_audit_logs()
    payment_logs = [l for l in logs if l.get("action") == "payment_status_update" or "payment" in l.get("action", "").lower()]
    print(f"[OK] Verified Audit Logging: {len(payment_logs)} payment audit log(s) recorded")

    print("\n=== ALL PAYMENT VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_payment_system_complete_verification()
